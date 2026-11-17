#!/usr/bin/env python3
"""Baixa a tabela agregada oficial SIA/SUS de SP no formato PRN do TABNET."""

from __future__ import annotations

import argparse
import re
import sys
from datetime import date
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import URLError
from urllib.parse import quote_from_bytes
from urllib.request import Request, urlopen

from sia_tabnet_data import ler_tabela_texto, mes_ordinal, rotulos_meses

FORM_URL = "https://tabnet.datasus.gov.br/cgi/deftohtm.exe?sia/cnv/qasp.def"
QUERY_URL = "https://tabnet.datasus.gov.br/cgi/tabcgi.exe?sia/cnv/qasp.def"
PADRAO_ARQUIVO = re.compile(r"^qasp(\d{2})(\d{2})\.dbf$", re.IGNORECASE)


class LeitorPeriodos(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._arquivos = False
        self.arquivos: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        atributos = dict(attrs)
        if tag.casefold() == "select":
            self._arquivos = (atributos.get("name") or "").casefold() == "arquivos"
        elif self._arquivos and tag.casefold() == "option":
            valor = atributos.get("value") or ""
            if PADRAO_ARQUIVO.fullmatch(valor):
                self.arquivos.append(valor)

    def handle_endtag(self, tag: str) -> None:
        if tag.casefold() == "select":
            self._arquivos = False


class LeitorPre(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._dentro = 0
        self.partes: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.casefold() == "pre":
            self._dentro += 1

    def handle_endtag(self, tag: str) -> None:
        if tag.casefold() == "pre" and self._dentro:
            self._dentro -= 1

    def handle_data(self, data: str) -> None:
        if self._dentro:
            self.partes.append(data)


def requisitar(url: str, data: bytes | None = None, timeout: int = 120) -> bytes:
    pedido = Request(
        url,
        data=data,
        headers={"User-Agent": "MovingHealth-SIA-Tabnet/1.0 (exportacao publica)"},
    )
    with urlopen(pedido, timeout=timeout) as resposta:
        return resposta.read()


def periodos_disponiveis(html: bytes) -> list[tuple[int, str]]:
    leitor = LeitorPeriodos()
    leitor.feed(html.decode("iso-8859-1"))
    periodos: list[tuple[int, str]] = []
    vistos: set[str] = set()
    for nome in leitor.arquivos:
        if nome.casefold() in vistos:
            continue
        vistos.add(nome.casefold())
        correspondencia = PADRAO_ARQUIVO.fullmatch(nome)
        assert correspondencia is not None
        ano = 2000 + int(correspondencia.group(1))
        mes = int(correspondencia.group(2))
        if ano < 2008 or mes < 1 or mes > 12:
            continue
        periodos.append((ano * 12 + mes - 1, nome))
    periodos.sort()
    if not periodos:
        raise ValueError("O TABNET não informou arquivos mensais qasp disponíveis.")
    ordinais = [ordinal for ordinal, _ in periodos]
    if any(b != a + 1 for a, b in zip(ordinais, ordinais[1:])):
        raise ValueError("Os arquivos disponíveis no TABNET têm lacunas mensais.")
    return periodos


def codificar_formulario(campos: list[tuple[str, str]]) -> bytes:
    """Codifica o formulário na codificação ISO-8859-1 usada pela página."""
    pares = []
    for chave, valor in campos:
        chave_codificada = quote_from_bytes(chave.encode("iso-8859-1"), safe="")
        valor_codificado = quote_from_bytes(valor.encode("iso-8859-1"), safe="")
        pares.append(f"{chave_codificada}={valor_codificado}")
    return "&".join(pares).encode("ascii")


def extrair_csv(resposta: bytes) -> str:
    pagina = resposta.decode("iso-8859-1")
    if "Tabela de conversao nao encontrada" in pagina:
        raise ValueError("O TABNET rejeitou a configuração da consulta.")
    leitor = LeitorPre()
    leitor.feed(pagina)
    texto = "".join(leitor.partes).strip("\r\n")
    if not texto:
        raise ValueError("O TABNET não retornou uma tabela PRN dentro de <pre>.")
    return texto


def baixar(destino: Path) -> tuple[Path, Path, int, str, str]:
    csv_path = destino / "tabnet_qasp_municipio_mes_qtd_aprovada.csv"
    html_path = destino / "tabnet_qasp_municipio_mes_qtd_aprovada_response.html"
    if csv_path.exists() or html_path.exists():
        raise FileExistsError(
            "A saída já existe. Preserve o arquivo bruto atual e escolha outro diretório; "
            "o baixador não sobrescreve fontes existentes."
        )

    pagina_formulario = requisitar(FORM_URL)
    periodos = periodos_disponiveis(pagina_formulario)
    campos = [
        ("Linha", "Município"),
        ("Coluna", "Ano/mês_atendimento"),
        ("Incremento", "Qtd.aprovada"),
        *(("Arquivos", nome) for _, nome in periodos),
        ("formato", "prn"),
        ("mostre", "Mostra"),
    ]
    resposta = requisitar(QUERY_URL, codificar_formulario(campos), timeout=180)
    csv_texto = extrair_csv(resposta)
    cabecalho, registros, _ = ler_tabela_texto(csv_texto, "resposta do TABNET")
    rotulos = rotulos_meses(cabecalho)
    esperados = [mes_ordinal(rotulo) for rotulo in rotulos]
    ordinais_solicitados = [ordinal for ordinal, _ in periodos]
    if esperados != ordinais_solicitados:
        raise ValueError(
            "Os meses retornados não correspondem aos arquivos solicitados; "
            "nenhum arquivo foi salvo."
        )
    if len(registros) < 600:
        raise ValueError(
            f"A tabela retornou apenas {len(registros)} linhas; nenhum arquivo foi salvo."
        )

    destino.mkdir(parents=True, exist_ok=True)
    csv_temp = csv_path.with_suffix(csv_path.suffix + ".tmp")
    html_temp = html_path.with_suffix(html_path.suffix + ".tmp")
    try:
        csv_temp.write_text(csv_texto + "\n", encoding="utf-8-sig", newline="")
        html_temp.write_bytes(resposta)
        csv_temp.replace(csv_path)
        html_temp.replace(html_path)
    finally:
        csv_temp.unlink(missing_ok=True)
        html_temp.unlink(missing_ok=True)

    return csv_path, html_path, len(registros), rotulos[0], rotulos[-1]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Baixa a consulta pública de produção ambulatorial SIA/SUS para SP."
    )
    parser.add_argument(
        "--destino",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "data/raw/sia_sus_sp",
        help="diretório de saída; arquivos existentes nunca são sobrescritos",
    )
    argumentos = parser.parse_args()
    try:
        csv_path, html_path, linhas, inicio, fim = baixar(argumentos.destino)
    except (OSError, URLError, TimeoutError, ValueError) as erro:
        print(f"Falha na obtenção/validação: {erro}", file=sys.stderr)
        return 2
    print(f"CSV: {csv_path.resolve()}")
    print(f"Resposta HTML original: {html_path.resolve()}")
    print(f"Linhas incluindo total: {linhas}")
    print(f"Período: {inicio} a {fim}")
    print(f"Data de acesso: {date.today().isoformat()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
