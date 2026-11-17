#!/usr/bin/env python3
"""Treina e avalia previsão municipal da quantidade aprovada do SIA/SUS."""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from collections import Counter
from datetime import date
from pathlib import Path

from sia_tabnet_data import (
    ler_tabela,
    mes_ordinal,
    parsear_contagem,
    rotulo_mes,
    rotulos_meses,
)

ARQUIVO_PADRAO = (
    Path(__file__).resolve().parents[1]
    / "data/raw/sia_sus_sp/tabnet_qasp_municipio_mes_qtd_aprovada.csv"
)
SAIDA_PROCESSADA = (
    Path(__file__).resolve().parents[1]
    / "data/processed/sia_sus_sp/qtd_aprovada_municipio_mes.csv"
)
SAIDA_RELATORIOS = Path(__file__).resolve().parents[1] / "reports/sia_sus_sp"
SAIDA_MODELO = Path(__file__).resolve().parents[1] / "models/moving_health_sia_sus.json"


def resolver_sistema(a: list[list[float]], b: list[float]) -> list[float]:
    """Resolve um sistema linear quadrado por eliminação de Gauss com pivô parcial."""
    n = len(b)
    matriz = [linha[:] + [b[i]] for i, linha in enumerate(a)]
    for coluna in range(n):
        pivo = max(range(coluna, n), key=lambda linha: abs(matriz[linha][coluna]))
        if abs(matriz[pivo][coluna]) < 1e-12:
            raise ValueError("A matriz do modelo ficou singular após validação.")
        matriz[coluna], matriz[pivo] = matriz[pivo], matriz[coluna]
        divisor = matriz[coluna][coluna]
        matriz[coluna] = [valor / divisor for valor in matriz[coluna]]
        for linha in range(n):
            if linha == coluna:
                continue
            fator = matriz[linha][coluna]
            if fator:
                matriz[linha] = [
                    atual - fator * base
                    for atual, base in zip(matriz[linha], matriz[coluna])
                ]
    return [matriz[i][-1] for i in range(n)]


def atributos(indice_tempo: int, centro: float, mes: int) -> list[float]:
    """Intercepto, tendência linear centrada e efeitos fixos para meses Jan–Nov."""
    efeitos_mensais = [1.0 if mes == candidato else 0.0 for candidato in range(11)]
    return [1.0, (indice_tempo - centro) / 12.0, *efeitos_mensais]


def ajustar_modelo(valores: list[int], mes_inicial: int) -> tuple[list[float], float]:
    """Ajusta tendência linear mais sazonalidade mensal por mínimos quadrados."""
    tamanho = len(valores)
    centro = (tamanho - 1) / 2
    amostras = [
        atributos(indice, centro, (mes_inicial + indice) % 12)
        for indice in range(tamanho)
    ]
    parametros = len(amostras[0])
    xtx = [[0.0] * parametros for _ in range(parametros)]
    xty = [0.0] * parametros
    for x, y in zip(amostras, valores):
        for i in range(parametros):
            xty[i] += x[i] * y
            for j in range(parametros):
                xtx[i][j] += x[i] * x[j]
    return resolver_sistema(xtx, xty), centro


def prever_modelo(
    parametros: list[float], centro: float, indice: int, mes_inicial: int
) -> float:
    x = atributos(indice, centro, (mes_inicial + indice) % 12)
    return max(0.0, sum(p * valor for p, valor in zip(parametros, x)))


def ler_painel(caminho: Path) -> tuple[list[str], dict[str, list[int]], Counter[str]]:
    cabecalho, linhas, indice_cabecalho = ler_tabela(caminho)
    meses = rotulos_meses(cabecalho)
    ordinais = [mes_ordinal(rotulo) for rotulo in meses]
    invalidos = [rotulo for rotulo, ordinal in zip(meses, ordinais) if ordinal is None]
    if invalidos or not ordinais:
        raise ValueError(f"Cabeçalhos mensais inválidos: {invalidos[:10]}")
    if any(b != a + 1 for a, b in zip(ordinais, ordinais[1:])):
        raise ValueError("Os cabeçalhos não formam uma sequência mensal contínua.")

    nomes = [linha[0].strip().strip('"') for linha in linhas]
    duplicados = sorted(
        nome for nome, quantidade in Counter(nome.casefold() for nome in nomes).items()
        if quantidade > 1 and not nome.startswith("total")
    )
    if duplicados:
        raise ValueError(f"Municípios duplicados na base: {duplicados[:10]}")

    municipio_para_valores: dict[str, list[int]] = {}
    ausencias_por_municipio: Counter[str] = Counter()
    totais = 0
    for numero_linha, linha in enumerate(linhas, start=indice_cabecalho + 2):
        municipio = linha[0].strip().strip('"')
        if municipio.casefold().startswith("total"):
            totais += 1
            continue
        valores: list[int] = []
        for numero_coluna, valor in enumerate(linha[1:1 + len(meses)], start=2):
            try:
                contagem = parsear_contagem(valor)
            except ValueError as erro:
                raise ValueError(
                    f"Valor inválido na linha {numero_linha}, coluna {numero_coluna}: {erro}"
                ) from erro
            if contagem is None:
                ausencias_por_municipio[municipio] += 1
            else:
                valores.append(contagem)
        if ausencias_por_municipio[municipio]:
            continue
        if len(valores) != len(meses):
            raise ValueError(
                f"Série incompleta para {municipio!r}: "
                f"{len(valores)} valores para {len(meses)} meses."
            )
        municipio_para_valores[municipio] = valores

    if totais > 1:
        raise ValueError(f"A tabela contém {totais} linhas de total.")
    if not municipio_para_valores:
        raise ValueError("Não há séries municipais completas para modelar.")
    return meses, municipio_para_valores, ausencias_por_municipio


def escrever_csv(caminho: Path, cabecalho: list[str], linhas: list[list[object]]) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with caminho.open("w", encoding="utf-8-sig", newline="") as arquivo:
        escritor = csv.writer(arquivo)
        escritor.writerow(cabecalho)
        escritor.writerows(linhas)


def escrever_json(caminho: Path, conteudo: dict[str, object]) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(
        json.dumps(conteudo, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def preparar_derivada(
    meses: list[str], series: dict[str, list[int]], caminho: Path
) -> None:
    linhas: list[list[object]] = []
    for municipio in sorted(series, key=str.casefold):
        for mes, valor in zip(meses, series[municipio]):
            ordinal = mes_ordinal(mes)
            assert ordinal is not None
            linhas.append([municipio, rotulo_mes(ordinal), valor])
    escrever_csv(caminho, ["municipio", "mes", "qtd_aprovada"], linhas)


def metricas(
    observacoes: list[int], previsoes: list[float]
) -> tuple[float, float, float | None, float | None]:
    if not observacoes:
        raise ValueError("Não há observações de avaliação.")
    erros = [real - previsto for real, previsto in zip(observacoes, previsoes)]
    mae = sum(abs(erro) for erro in erros) / len(erros)
    rmse = math.sqrt(sum(erro * erro for erro in erros) / len(erros))
    total_real = sum(observacoes)
    wape = sum(abs(erro) for erro in erros) / total_real if total_real else None
    media_real = sum(observacoes) / len(observacoes)
    variacao_total = sum((real - media_real) ** 2 for real in observacoes)
    r2 = (
        1.0 - sum(erro * erro for erro in erros) / variacao_total
        if variacao_total
        else None
    )
    return mae, rmse, wape, r2


def executar(
    entrada: Path,
    saida_processada: Path,
    saida_relatorios: Path,
    horizonte_teste: int,
    horizonte_futuro: int,
    minimo_treino: int,
    saida_modelo: Path,
) -> None:
    if not entrada.is_file():
        raise FileNotFoundError(
            f"CSV bruto ausente: {entrada}. Rode scripts/download_sia_tabnet.py primeiro."
        )
    if horizonte_teste < 1 or horizonte_teste > 12:
        raise ValueError("O horizonte de avaliação deve ficar entre 1 e 12 meses.")
    if horizonte_futuro < 1 or horizonte_futuro > 12:
        raise ValueError("O horizonte futuro deve ficar entre 1 e 12 meses.")
    if minimo_treino < 13:
        raise ValueError("São necessários pelo menos 13 meses para estimar a sazonalidade.")

    meses, series, ausencias = ler_painel(entrada)
    if len(meses) < minimo_treino + horizonte_teste:
        raise ValueError(
            f"Há {len(meses)} meses; são necessários pelo menos "
            f"{minimo_treino + horizonte_teste} para a avaliação definida."
        )
    preparar_derivada(meses, series, saida_processada)
    ordinal_inicial = mes_ordinal(meses[0])
    assert ordinal_inicial is not None
    mes_inicial = ordinal_inicial % 12

    elegiveis = {
        municipio: valores
        for municipio, valores in series.items()
        if len(valores) >= minimo_treino + horizonte_teste
    }
    if not elegiveis:
        raise ValueError("Nenhum município tem histórico suficiente para avaliação.")

    observacoes: list[int] = []
    previsoes_baseline: list[float] = []
    previsoes_modelo: list[float] = []
    previsoes_validacao: list[list[object]] = []
    corte = len(meses) - horizonte_teste
    for municipio in sorted(elegiveis, key=str.casefold):
        valores = elegiveis[municipio]
        treino = valores[:corte]
        parametros, centro = ajustar_modelo(treino, mes_inicial)
        for indice in range(corte, len(valores)):
            real = valores[indice]
            baseline = float(valores[indice - 12])
            previsto = prever_modelo(parametros, centro, indice, mes_inicial)
            ordinal = mes_ordinal(meses[indice])
            assert ordinal is not None
            previsoes_validacao.append(
                [municipio, rotulo_mes(ordinal), real, baseline, previsto]
            )
            observacoes.append(real)
            previsoes_baseline.append(baseline)
            previsoes_modelo.append(previsto)

    metricas_por_modelo: dict[
        str, tuple[float, float, float | None, float | None]
    ] = {}
    linhas_metricas: list[list[object]] = []
    for nome, previsoes in (
        ("baseline_sazonal_12_meses", previsoes_baseline),
        ("tendencia_linear_sazonalidade_mensal", previsoes_modelo),
    ):
        mae, rmse, wape, r2 = metricas(observacoes, previsoes)
        metricas_por_modelo[nome] = (mae, rmse, wape, r2)
        linhas_metricas.append(
            [
                nome,
                len(observacoes),
                len(elegiveis),
                f"{mae:.6f}",
                f"{rmse:.6f}",
                "" if wape is None else f"{wape:.8f}",
                "" if r2 is None else f"{r2:.8f}",
            ]
        )

    metricas_path = saida_relatorios / "metricas_avaliacao.csv"
    validacao_path = saida_relatorios / "previsoes_validacao.csv"
    futuro_path = saida_relatorios / "previsoes_futuras.csv"
    cobertura_path = saida_relatorios / "cobertura.csv"
    excluidos_path = saida_relatorios / "municipios_excluidos.csv"
    escrever_csv(
        metricas_path,
        ["modelo", "observacoes", "municipios", "mae", "rmse", "wape", "r2"],
        linhas_metricas,
    )
    escrever_csv(
        validacao_path,
        ["municipio", "mes", "valor_real", "baseline_sazonal_12_meses", "previsao_modelo"],
        previsoes_validacao,
    )
    escrever_csv(
        cobertura_path,
        [
            "periodo_inicio",
            "periodo_fim",
            "meses",
            "municipios_com_linha",
            "municipios_com_serie_completa",
            "municipios_com_celula_vazia",
            "municipios_avaliados",
            "horizonte_teste_meses",
            "meses_minimos_de_treino",
        ],
        [[
            meses[0],
            meses[-1],
            len(meses),
            len(series) + len(ausencias),
            len(series),
            len(ausencias),
            len(elegiveis),
            horizonte_teste,
            minimo_treino,
        ]],
    )
    escrever_csv(
        excluidos_path,
        ["municipio", "celulas_vazias", "motivo"],
        [
            [municipio, quantidade, "série com célula vazia; valor não imputado"]
            for municipio, quantidade in sorted(
                ausencias.items(), key=lambda item: item[0].casefold()
            )
        ],
    )

    metricas_com_wape = {
        nome: valores
        for nome, valores in metricas_por_modelo.items()
        if valores[2] is not None
    }
    modelo_recomendado = min(
        metricas_com_wape,
        key=lambda nome: metricas_com_wape[nome][2],  # type: ignore[index]
    )

    previsoes_futuras: list[list[object]] = []
    series_exportadas: list[dict[str, object]] = []
    ultimo_ordinal = mes_ordinal(meses[-1])
    assert ultimo_ordinal is not None
    for municipio in sorted(elegiveis, key=str.casefold):
        valores = elegiveis[municipio]
        parametros, centro = ajustar_modelo(valores, mes_inicial)
        series_exportadas.append(
            {
                "municipio": municipio,
                "observacoes_treino": len(valores),
                "ultimos_12_valores": valores[-12:],
                "parametros_tendencia_sazonal": parametros,
                "centro_tendencia": centro,
                "mes_inicial_indice": mes_inicial,
            }
        )
        for passo in range(1, horizonte_futuro + 1):
            indice = len(valores) - 1 + passo
            previsao_modelo = prever_modelo(parametros, centro, indice, mes_inicial)
            previsao_baseline = valores[-12 + ((passo - 1) % 12)]
            previsao_recomendada = (
                previsao_baseline
                if modelo_recomendado == "baseline_sazonal_12_meses"
                else int(math.floor(previsao_modelo + 0.5))
            )
            previsoes_futuras.append(
                [
                    municipio,
                    rotulo_mes(ultimo_ordinal + passo),
                    previsao_baseline,
                    int(math.floor(previsao_modelo + 0.5)),
                    previsao_recomendada,
                    modelo_recomendado,
                ]
            )
    escrever_csv(
        futuro_path,
        [
            "municipio",
            "mes",
            "previsao_baseline_sazonal_12_meses",
            "previsao_ml_tendencia_sazonal",
            "previsao_recomendada",
            "modelo_recomendado",
        ],
        previsoes_futuras,
    )

    modelo_artifact = {
        "versao_formato": 1,
        "data_treinamento": date.today().isoformat(),
        "fonte": "SIA/SUS TABNET — São Paulo, Município x mês de atendimento, Qtd.aprovada",
        "periodo_dados_inicio": meses[0],
        "periodo_dados_fim": meses[-1],
        "alvo": "quantidade aprovada de procedimentos ambulatoriais",
        "aviso_alvo": (
            "Não representa pessoas, solicitações de transporte, viagens, corridas "
            "ou necessidade clínica."
        ),
        "horizonte_maximo_meses": horizonte_futuro,
        "modelo_recomendado_na_validacao": modelo_recomendado,
        "metricas_holdout": {
            nome: {
                "mae": valores[0],
                "rmse": valores[1],
                "wape": valores[2],
                "r2": valores[3],
            }
            for nome, valores in metricas_por_modelo.items()
        },
        "municipios": series_exportadas,
    }
    escrever_json(saida_modelo, modelo_artifact)

    linhas_ausentes = sum(bool(quantidade) for quantidade in ausencias.values())
    print(f"Período: {meses[0]} a {meses[-1]} ({len(meses)} meses)")
    print(f"Municípios com série completa e histórico suficiente: {len(elegiveis)}")
    print(f"Municípios com células vazias excluídos: {linhas_ausentes}")
    print(f"Corte temporal: {meses[corte]} a {meses[-1]}")
    print(f"Métricas: {metricas_path.resolve()}")
    print(f"Cobertura: {cobertura_path.resolve()}")
    print(f"Municípios excluídos: {excluidos_path.resolve()}")
    print(f"Previsões de avaliação: {validacao_path.resolve()}")
    print(f"Previsões futuras indicativas: {futuro_path.resolve()}")
    print(f"Modelo recomendado no holdout: {modelo_recomendado}")
    print(f"Artefato do modelo treinado: {saida_modelo.resolve()}")
    print(f"Tabela longa derivada: {saida_processada.resolve()}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Valida, deriva, treina e avalia previsão de Qtd.aprovada do SIA/SUS. "
            "Não estima viagens, pessoas ou necessidade clínica."
        )
    )
    parser.add_argument("--input", type=Path, default=ARQUIVO_PADRAO)
    parser.add_argument("--output-processed", type=Path, default=SAIDA_PROCESSADA)
    parser.add_argument("--output-reports", type=Path, default=SAIDA_RELATORIOS)
    parser.add_argument("--output-model", type=Path, default=SAIDA_MODELO)
    parser.add_argument("--test-horizon", type=int, default=12)
    parser.add_argument("--forecast-horizon", type=int, default=12)
    parser.add_argument("--min-train-months", type=int, default=36)
    argumentos = parser.parse_args()
    try:
        executar(
            argumentos.input,
            argumentos.output_processed,
            argumentos.output_reports,
            argumentos.test_horizon,
            argumentos.forecast_horizon,
            argumentos.min_train_months,
            argumentos.output_model,
        )
    except (OSError, csv.Error, ValueError) as erro:
        print(f"Treino interrompido: {erro}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
