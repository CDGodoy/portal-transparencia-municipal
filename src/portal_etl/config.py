"""Configuração central do pipeline: caminhos, municípios monitorados e parâmetros."""

from __future__ import annotations

import csv
import os
from dataclasses import dataclass
from datetime import date
from functools import lru_cache
from pathlib import Path


def _find_root() -> Path:
    env = os.getenv("PORTAL_ROOT")
    if env:
        return Path(env).resolve()
    here = Path(__file__).resolve()
    for parent in here.parents:
        if (parent / "pyproject.toml").exists() and (parent / "transform").exists():
            return parent
    return Path.cwd().resolve()


ROOT = _find_root()
DATA_DIR = Path(os.getenv("PORTAL_DATA_DIR", ROOT / "data"))
BRONZE_DIR = Path(os.getenv("PORTAL_BRONZE_DIR", DATA_DIR / "bronze"))
WAREHOUSE_PATH = Path(os.getenv("PORTAL_DUCKDB_PATH", DATA_DIR / "warehouse" / "portal.duckdb"))
DBT_DIR = ROOT / "transform"
SITE_DATA_DIR = Path(os.getenv("PORTAL_SITE_DATA_DIR", ROOT / "site" / "public" / "data"))
MUNICIPIOS_CSV = DBT_DIR / "seeds" / "municipios.csv"

# Primeiro exercício com RREO consistente no SICONFI para os municípios monitorados.
ANO_INICIAL = int(os.getenv("PORTAL_ANO_INICIAL", "2016"))
# PNCP passou a ser obrigatório para municípios a partir de 2023 (Lei 14.133/2021).
ANO_INICIAL_PNCP = int(os.getenv("PORTAL_ANO_INICIAL_PNCP", "2023"))


@dataclass(frozen=True)
class Municipio:
    cod_ibge: int
    nome: str
    uf: str
    cnpj: str
    slug: str
    destaque: bool = False


@lru_cache
def carregar_municipios(path: Path = MUNICIPIOS_CSV) -> tuple[Municipio, ...]:
    with open(path, encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    return tuple(
        Municipio(
            cod_ibge=int(r["cod_ibge"]),
            nome=r["nome"],
            uf=r["uf"],
            cnpj=r["cnpj"].zfill(14),
            slug=r["slug"],
            destaque=r.get("destaque", "false").lower() == "true",
        )
        for r in rows
    )


def ano_corrente() -> int:
    return int(os.getenv("PORTAL_ANO_CORRENTE", date.today().year))
