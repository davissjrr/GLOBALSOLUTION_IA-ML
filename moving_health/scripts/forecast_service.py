#!/usr/bin/env python3
"""API local de demonstração para consultar previsões do Moving Health."""

from __future__ import annotations

import argparse
import json
import math
import re
import unicodedata
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from sia_tabnet_data import mes_ordinal, rotulo_mes
from train_sia_forecast import prever_modelo

RAIZ_PROJETO = Path(__file__).resolve().parents[1]
MODELO_PADRAO = RAIZ_PROJETO / "models/moving_health_sia_sus.json"


def normalizar_municipio(nome: str) -> str:
    texto = unicodedata.normalize("NFKD", nome)
    sem_acentos = "".join(caractere for caractere in texto if not unicodedata.combining(caractere))
    sem_codigo = re.sub(r"^\s*\d{6}\s+", "", sem_acentos)
    return re.sub(r"[^a-zA-Z0-9]+", " ", sem_codigo).strip().casefold()


def carregar_artifact(caminho: Path) -> dict[str, object]:
    with caminho.open(encoding="utf-8") as arquivo:
        artifact = json.load(arquivo)
    if artifact.get("versao_formato") != 1:
        raise ValueError("Versão de artefato de modelo não reconhecida.")
    return artifact


def gerar_previsao(
    artifact: dict[str, object], municipio: str, horizonte: int, estrategia: str
) -> dict[str, object]:
    maximo = int(artifact["horizonte_maximo_meses"])
    if not 1 <= horizonte <= maximo:
        raise ValueError(f"O horizonte deve estar entre 1 e {maximo} meses.")

    municipios = artifact["municipios"]
    chave = normalizar_municipio(municipio)
    serie = next(
        (
            item
            for item in municipios
            if normalizar_municipio(str(item["municipio"])) == chave
        ),
        None,
    )
    if serie is None:
        raise KeyError(f"Município não encontrado: {municipio}")

    recomendado = str(artifact["modelo_recomendado_na_validacao"])
    if estrategia in {"selecionado", "recomendado"}:
        modelo = recomendado
    elif estrategia in {"baseline", "baseline_sazonal_12_meses"}:
        modelo = "baseline_sazonal_12_meses"
    elif estrategia in {"experimental", "tendencia_sazonal"}:
        modelo = "tendencia_linear_sazonalidade_mensal"
    else:
        raise ValueError(
            "Modelo desconhecido. Use selecionado, baseline ou experimental."
        )

    ultimo_ordinal = mes_ordinal(str(artifact["periodo_dados_fim"]))
    if ultimo_ordinal is None:
        raise ValueError("O artefato contém um último mês inválido.")

    parametros = [float(v) for v in serie["parametros_tendencia_sazonal"]]
    centro = float(serie["centro_tendencia"])
    mes_inicial = int(serie["mes_inicial_indice"])
    observacoes = int(serie["observacoes_treino"])
    ultimos_12 = [int(valor) for valor in serie["ultimos_12_valores"]]

    previsoes = []
    for passo in range(1, horizonte + 1):
        indice_modelo = observacoes - 1 + passo
        previsao_ml = int(
            math.floor(
                prever_modelo(parametros, centro, indice_modelo, mes_inicial) + 0.5
            )
        )
        previsao_baseline = ultimos_12[(passo - 1) % 12]
        valor = (
            previsao_baseline
            if modelo == "baseline_sazonal_12_meses"
            else previsao_ml
        )
        previsoes.append(
            {
                "mes": rotulo_mes(ultimo_ordinal + passo),
                "qtd_aprovada_estimada": valor,
            }
        )

    metricas = artifact["metricas_holdout"].get(modelo, {})
    return {
        "municipio": str(serie["municipio"]),
        "indicador": "quantidade aprovada de procedimentos ambulatoriais",
        "modelo": modelo,
        "status_modelo": "referência de comparação" if modelo.startswith("baseline") else "experimental",
        "periodo_dados_fim": artifact["periodo_dados_fim"],
        "horizonte_meses": horizonte,
        "metricas_holdout": metricas,
        "previsoes": previsoes,
        "aviso": str(artifact["aviso_alvo"]),
    }


def criar_handler(artifact: dict[str, object]) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        server_version = "MovingHealthForecast/1.0"

        def responder(self, status: int, conteudo: dict[str, object]) -> None:
            corpo = json.dumps(conteudo, ensure_ascii=False, indent=2).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(corpo)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(corpo)

        def do_GET(self) -> None:  # noqa: N802 - nome exigido por BaseHTTPRequestHandler
            rota = urlsplit(self.path)
            if rota.path == "/health":
                self.responder(
                    200,
                    {
                        "status": "ok",
                        "artefato": str(MODELO_PADRAO.name),
                        "modelo_recomendado": artifact[
                            "modelo_recomendado_na_validacao"
                        ],
                    },
                )
                return
            if rota.path != "/previsao":
                self.responder(
                    404,
                    {
                        "erro": "Rota não encontrada.",
                        "rotas": ["/health", "/previsao?municipio=São%20Paulo"],
                    },
                )
                return

            consulta = parse_qs(rota.query, keep_blank_values=True)
            municipio = consulta.get("municipio", [""])[0].strip()
            if not municipio:
                self.responder(
                    400,
                    {"erro": "Informe o parâmetro municipio."},
                )
                return
            try:
                horizonte = int(consulta.get("horizonte", ["12"])[0])
                estrategia = consulta.get("modelo", ["selecionado"])[0]
                resultado = gerar_previsao(
                    artifact, municipio, horizonte, estrategia
                )
            except ValueError as erro:
                self.responder(400, {"erro": str(erro)})
                return
            except KeyError as erro:
                self.responder(404, {"erro": str(erro).strip("'")})
                return
            self.responder(200, resultado)

        def log_message(self, formato: str, *args: object) -> None:
            print(f"{self.address_string()} - {formato % args}")

    return Handler


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Disponibiliza uma API local de previsões indicativas do SIA/SUS."
    )
    parser.add_argument("--model", type=Path, default=MODELO_PADRAO)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    argumentos = parser.parse_args()
    try:
        artifact = carregar_artifact(argumentos.model)
    except (OSError, json.JSONDecodeError, ValueError) as erro:
        parser.error(f"Não foi possível carregar o modelo: {erro}")

    servidor = ThreadingHTTPServer(
        (argumentos.host, argumentos.port), criar_handler(artifact)
    )
    print(f"API local em http://{argumentos.host}:{argumentos.port}")
    print(f"Alvo previsto: {artifact['alvo']}")
    print(
        "Atenção: previsão agregada de produção assistencial; "
        "não prevê viagens ou corridas."
    )
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("Encerrando API.")
    finally:
        servidor.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
