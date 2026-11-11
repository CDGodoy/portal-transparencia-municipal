"""Execução programática do dbt (sem depender do PATH do shell)."""

from __future__ import annotations

import os

from . import config


def run_dbt(args: list[str]) -> bool:
    from dbt.cli.main import dbtRunner

    config.WAREHOUSE_PATH.parent.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("PORTAL_DUCKDB_PATH", str(config.WAREHOUSE_PATH))
    os.environ.setdefault("PORTAL_BRONZE_DIR", str(config.BRONZE_DIR))
    full = [
        *args,
        "--project-dir",
        str(config.DBT_DIR),
        "--profiles-dir",
        str(config.DBT_DIR),
    ]
    result = dbtRunner().invoke(full)
    return bool(result.success)
