#!/usr/bin/env python3
"""Leitura e validação estrutural da exportação PRN do TABNET SIA/SUS."""

from __future__ import annotations

import csv
import re
from pathlib import Path

MESES = ("Jan", "Fev", "Mar", "Abr", "Mai", "Jun",
         "Jul", "Ago", "Set", "Out", "Nov", "Dez")
MES_RE = re.compile(r"^(\d{4})/(" + "|".join(MESES) + r")$")
CONTAGEM_RE = re.compile(r"^(?:\d+|\d{1,3}(?:\.\d{3})+)$")
MARCADORES_ZERO = {"-", "\u2013", "\u2014"}
CABECALHO_MUNICIPIO = "Munic\u00edpio"


def ler_texto(caminho: Path) -> str:
    """Lê UTF-8 (com ou sem BOM) ou a codificação legada ISO-8859-1."""
    conteudo = caminho.read_bytes()
    try:
        return conteudo.decode("utf-8-sig")
    except UnicodeDecodeError:
        return conteudo.decode("iso-8859-1")


def mes_ordinal(rotulo: str) -> int | None:
    correspondencia = MES_RE.fullmatch(rotulo.strip().strip('"'))
    if not correspondencia:
        return None
    ano, mes = correspondencia.groups()
    return int(ano) * 12 + MESES.index(mes)


def rotulo_mes(ordinal: int) -> str:
    ano, mes_zero_based = divmod(ordinal, 12)
    return f"{ano:04d}-{mes_zero_based + 1:02d}"


def rotulos_meses(cabecalho: list[str]) -> list[str]:
    """Retorna apenas meses; o total geral opcional não é uma observação mensal."""
    rotulos = cabecalho[1:]
    if rotulos and rotulos[-1].strip().strip('"').casefold() == "total":
        rotulos = rotulos[:-1]
    return rotulos


def parsear_contagem(valor: str) -> int | None:
    """Converte contagem TABNET; marcador "-" significa zero, vazio é ausente."""
    valor = valor.strip()
    if valor == "":
        return None
    if valor in MARCADORES_ZERO:
        return 0
    if not CONTAGEM_RE.fullmatch(valor):
        raise ValueError(f"valor de contagem inválido: {valor!r}")
    return int(valor.replace(".", ""))


def ler_tabela_texto(texto: str, origem: str = "entrada") -> tuple[list[str], list[list[str]], int]:
    """Localiza e lê a tabela Município × mês dentro do texto PRN."""
    linhas = texto.splitlines()
    indice_cabecalho = None
    cabecalho = None

    for indice, linha in enumerate(linhas):
        try:
            campos = next(csv.reader([linha], delimiter=";"))
        except csv.Error:
            continue
        if (
            len(campos) >= 2
            and campos[0].lstrip("\ufeff").strip().strip('"').casefold()
            == CABECALHO_MUNICIPIO.casefold()
            and mes_ordinal(campos[1]) is not None
            and all(mes_ordinal(rotulo) is not None for rotulo in rotulos_meses(campos))
        ):
            indice_cabecalho = indice
            cabecalho = campos
            break

    if indice_cabecalho is None or cabecalho is None:
        raise ValueError(
            f"{origem}: não encontrei o cabeçalho Município seguido por meses AAAA/Mês."
        )

    registros: list[list[str]] = []
    for numero, linha in enumerate(linhas[indice_cabecalho + 1:], start=indice_cabecalho + 2):
        if not linha.strip():
            break
        try:
            campos = next(csv.reader([linha], delimiter=";"))
        except csv.Error as erro:
            raise ValueError(f"{origem}: erro CSV na linha {numero}: {erro}") from erro
        if len(campos) != len(cabecalho):
            raise ValueError(
                f"{origem}: linha {numero} tem {len(campos)} campos; "
                f"o cabeçalho tem {len(cabecalho)}."
            )
        registros.append(campos)
        if campos[0].strip().strip('"').casefold().startswith("total"):
            break

    if not registros:
        raise ValueError(f"{origem}: encontrei o cabeçalho, mas nenhuma linha de dados.")
    return cabecalho, registros, indice_cabecalho


def ler_tabela(caminho: Path) -> tuple[list[str], list[list[str]], int]:
    return ler_tabela_texto(ler_texto(caminho), str(caminho))
