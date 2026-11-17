#!/usr/bin/env python3
"""Gera contagens horárias sintéticas para demonstrar demanda do Moving Health.

Os valores deste módulo são hipóteses de simulação; não são registros de viagens
reais nem estimativas observadas do Moving Health.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

ZONAS = ("zona_01", "zona_02", "zona_03", "zona_04", "zona_05", "zona_06")
SERVICOS = {
    "transporte_paciente": 1.0,
    "visita_profissional": 0.7,
}
TAXA_BASE_POR_ZONA = (0.55, 0.75, 1.05, 0.45, 1.15, 0.65)
VEICULOS_BASE_POR_ZONA = (1, 1, 2, 1, 2, 1)
FORMA_DISTRIBUICAO = "Poisson com taxa latente Gamma (sobre-dispersão)"
SEMENTE_PADRAO = 2026


def _fator_horario(horas: np.ndarray) -> np.ndarray:
    return np.select(
        [
            (horas >= 6) & (horas <= 9),
            (horas >= 10) & (horas <= 15),
            (horas >= 16) & (horas <= 19),
            (horas >= 20) | (horas <= 5),
        ],
        [1.8, 1.15, 1.55, 0.45],
        default=1.0,
    ).astype(float)


def gerar_dados_sinteticos(
    dias: int = 90,
    semente: int = SEMENTE_PADRAO,
    multiplicador_demanda: float = 1.0,
    multiplicador_frota: float = 1.0,
    inicio: str = "2025-01-01",
    cenario: str = "base",
) -> pd.DataFrame:
    """Gera uma linha por hora × zona × tipo de serviço, sem dados pessoais."""
    if dias < 1:
        raise ValueError("O horizonte simulado deve ter ao menos um dia.")
    if multiplicador_demanda <= 0 or multiplicador_frota < 0:
        raise ValueError("Demanda deve ser positiva e frota não pode ser negativa.")

    rng = np.random.default_rng(semente)
    timestamps = pd.date_range(start=inicio, periods=dias * 24, freq="h")
    horas = timestamps.hour.to_numpy()
    dias_semana = timestamps.dayofweek.to_numpy()
    fator_hora = _fator_horario(horas)
    fator_semana = np.where(dias_semana < 5, 1.0, 0.72)
    fator_turno_frota = np.where((horas >= 6) & (horas <= 21), 1.0, 0.55)

    partes: list[pd.DataFrame] = []
    for indice_zona, zona in enumerate(ZONAS):
        taxa_base = TAXA_BASE_POR_ZONA[indice_zona]
        frota_base = VEICULOS_BASE_POR_ZONA[indice_zona]
        for servico, fator_servico in SERVICOS.items():
            taxa_media = (
                taxa_base
                * fator_servico
                * fator_hora
                * fator_semana
                * multiplicador_demanda
            )
            # Gamma-Poisson permite picos aleatórios acima da variação Poisson simples.
            taxa_latente = rng.gamma(shape=8.0, scale=taxa_media / 8.0)
            pedidos = rng.poisson(lam=taxa_latente).astype("int64")

            veiculos = np.floor(
                frota_base * fator_turno_frota * multiplicador_frota
            ).astype("int64")
            capacidade = veiculos  # hipótese: 1 solicitação atendível por veículo/hora
            atendidos = np.minimum(pedidos, capacidade)

            partes.append(
                pd.DataFrame(
                    {
                        "timestamp": timestamps,
                        "zone_id": zona,
                        "service_type": servico,
                        "hour": horas,
                        "weekday": dias_semana,
                        "is_weekend": (dias_semana >= 5).astype("int8"),
                        "trips_requested": pedidos,
                        "vehicles_available": veiculos,
                        "trip_capacity": capacidade,
                        "trips_served": atendidos,
                        "unmet_requests": pedidos - atendidos,
                        "scenario": cenario,
                        "is_synthetic": True,
                    }
                )
            )

    return pd.concat(partes, ignore_index=True).sort_values(
        ["timestamp", "zone_id", "service_type"], ignore_index=True
    )


def salvar_csv(
    destino: Path,
    dias: int = 90,
    semente: int = SEMENTE_PADRAO,
    multiplicador_demanda: float = 1.0,
    multiplicador_frota: float = 1.0,
    inicio: str = "2025-01-01",
    cenario: str = "base",
) -> pd.DataFrame:
    dados = gerar_dados_sinteticos(
        dias=dias,
        semente=semente,
        multiplicador_demanda=multiplicador_demanda,
        multiplicador_frota=multiplicador_frota,
        inicio=inicio,
        cenario=cenario,
    )
    destino.parent.mkdir(parents=True, exist_ok=True)
    dados.to_csv(destino, index=False, encoding="utf-8-sig")
    return dados


def main() -> int:
    raiz = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(
        description="Gera dados sintéticos de demanda horária para experimento didático."
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=raiz / "data/synthetic/moving_health_pedidos_sinteticos.csv",
    )
    parser.add_argument("--days", type=int, default=90)
    parser.add_argument("--seed", type=int, default=SEMENTE_PADRAO)
    parser.add_argument("--demand-multiplier", type=float, default=1.0)
    parser.add_argument("--fleet-multiplier", type=float, default=1.0)
    parser.add_argument("--start", default="2025-01-01")
    argumentos = parser.parse_args()
    try:
        dados = salvar_csv(
            destino=argumentos.output,
            dias=argumentos.days,
            semente=argumentos.seed,
            multiplicador_demanda=argumentos.demand_multiplier,
            multiplicador_frota=argumentos.fleet_multiplier,
            inicio=argumentos.start,
        )
    except (OSError, ValueError) as erro:
        parser.error(str(erro))
    print(f"CSV sintético: {argumentos.output.resolve()}")
    print(f"Linhas: {len(dados)}; semente: {argumentos.seed}; horizonte: {argumentos.days} dias")
    print("Todos os registros estão marcados como sintéticos; não são corridas observadas.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
