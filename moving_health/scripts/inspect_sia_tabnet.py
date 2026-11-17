#!/usr/bin/env python3
"""Inspeciona dimensões e consistência da exportação CSV do TabNet SIA/SUS."""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path

from sia_tabnet_data import (
    MARCADORES_ZERO,
    ler_tabela,
    mes_ordinal,
    parsear_contagem,
    rotulos_meses,
)


def inspecionar(caminho: Path) -> int:
    cabecalho, registros, indice_cabecalho = ler_tabela(caminho)
    meses = rotulos_meses(cabecalho)
    ordinais = [mes_ordinal(rotulo) for rotulo in meses]
    invalidos = [
        rotulo for rotulo, ordinal in zip(meses, ordinais) if ordinal is None
    ]
    sequencial = (
        bool(ordinais)
        and not invalidos
        and all(b == a + 1 for a, b in zip(ordinais, ordinais[1:]))
    )

    nomes = [linha[0].strip().strip('"') for linha in registros]
    totais = [nome for nome in nomes if nome.casefold().startswith("total")]
    municipios = [
        nome for nome in nomes if not nome.casefold().startswith("total")
    ]
    duplicados = sorted(
        nome for nome, quantidade in Counter(municipios).items()
        if quantidade > 1
    )

    celulas_vazias = 0
    marcadores_zero = 0
    valores_irregulares: list[tuple[int, int, str]] = []
    total_irregulares = 0
    for numero, linha in enumerate(registros, start=indice_cabecalho + 2):
        if linha[0].strip().strip('"').casefold().startswith("total"):
            continue
        for coluna, valor in enumerate(linha[1:1 + len(meses)], start=2):
            valor = valor.strip()
            if valor == "":
                celulas_vazias += 1
            elif valor in MARCADORES_ZERO:
                marcadores_zero += 1
            else:
                try:
                    parsear_contagem(valor)
                except ValueError:
                    total_irregulares += 1
                    if len(valores_irregulares) < 10:
                        valores_irregulares.append((numero, coluna, valor))

    print(f"Arquivo: {caminho.resolve()}")
    print(
        f"Dimensão da tabela: {len(registros)} linhas de dados x "
        f"{len(cabecalho)} colunas (inclui total geral se presente)"
    )
    print(f"Linhas anteriores ao cabeçalho: {indice_cabecalho}")
    if meses:
        print(f"Período nas colunas: {meses[0]} a {meses[-1]}")
    print(f"Colunas mensais: {len(meses)}; sequência mensal contínua: {sequencial}")
    print(f"Linhas de municípios: {len(municipios)}")
    print(f"Linhas de total: {len(totais)}")
    print(f"Rótulos de município repetidos: {len(duplicados)}")
    print(f"Células realmente vazias: {celulas_vazias}")
    print(f"Marcadores TABNET tratados como zero: {marcadores_zero}")
    print(f"Valores fora do padrão inteiro: {total_irregulares}")
    if invalidos:
        print(f"Rótulos de mês não reconhecidos: {invalidos[:10]}")
    if duplicados:
        print(f"Amostra de duplicados: {duplicados[:10]}")
    if valores_irregulares:
        print(f"Amostra de valores: {valores_irregulares}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Inspeciona a exportação TABNET SIA/SUS antes da modelagem."
    )
    parser.add_argument(
        "csv",
        nargs="?",
        type=Path,
        default=Path(__file__).resolve().parents[1]
        / "data/raw/sia_sus_sp/tabnet_qasp_municipio_mes_qtd_aprovada.csv",
        help="caminho para a exportação CSV",
    )
    argumentos = parser.parse_args()
    try:
        return inspecionar(argumentos.csv)
    except (OSError, ValueError) as erro:
        parser.error(str(erro))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
