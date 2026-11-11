"""Camada bronze: grava as respostas das APIs como chegaram (NDJSON.gz), particionadas por
fonte/dataset/chaves, com metadados de linhagem. Os caminhos são determinísticos, então
re-ingerir o mesmo relatório sobrescreve o arquivo (idempotência, sem duplicatas).

O manifesto guarda a "versão" de cada relatório (data de entrega/retificação no SICONFI ou
data de atualização no PNCP) para permitir ingestão incremental.
"""

from __future__ import annotations

import gzip
import json
import os
import tempfile
from collections.abc import Iterable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def _slug(value: Any) -> str:
    return str(value).replace(" ", "_").replace("/", "-")


class BronzeStore:
    def __init__(self, root: Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.manifest_path = self.root / "_manifest.json"
        self._manifest: dict[str, dict[str, Any]] = self._load_manifest()

    # ---------------------------------------------------------------- paths
    def path_for(self, source: str, dataset: str, partitions: dict[str, Any]) -> Path:
        parts = [f"{k}={_slug(v)}" for k, v in partitions.items()]
        return self.root.joinpath(source, dataset, *parts, "data.ndjson.gz")

    def exists(self, source: str, dataset: str, partitions: dict[str, Any]) -> bool:
        return self.path_for(source, dataset, partitions).exists()

    # ---------------------------------------------------------------- write
    def write(
        self,
        source: str,
        dataset: str,
        partitions: dict[str, Any],
        records: Iterable[dict[str, Any]],
        source_url: str,
    ) -> int:
        path = self.path_for(source, dataset, partitions)
        path.parent.mkdir(parents=True, exist_ok=True)
        ingested_at = datetime.now(UTC).isoformat(timespec="seconds")
        n = 0
        # Escrita atômica: arquivo temporário + rename, para nunca deixar parquet/ndjson parcial.
        fd, tmp = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
        os.close(fd)
        try:
            # mtime=0 deixa o gzip determinístico (mesmo conteúdo => mesmo arquivo => diff limpo).
            with (
                open(tmp, "wb") as raw,
                gzip.GzipFile(filename="", fileobj=raw, mode="wb", mtime=0) as gz,
            ):
                for ordem, rec in enumerate(records):
                    row = dict(rec)
                    row["_ordem"] = ordem
                    row["_source_url"] = source_url
                    gz.write((json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n").encode())
                    n += 1
            os.replace(tmp, path)
        finally:
            if os.path.exists(tmp):
                os.remove(tmp)
        self._meta_log(source, dataset, partitions, n, ingested_at)
        return n

    def _meta_log(self, source, dataset, partitions, n, ingested_at) -> None:
        key = "|".join([source, dataset, *[f"{k}={v}" for k, v in partitions.items()]])
        entry = self._manifest.setdefault(key, {})
        entry.update({"rows": n, "ingested_at": ingested_at})

    # ------------------------------------------------------------- manifest
    def _load_manifest(self) -> dict[str, dict[str, Any]]:
        if self.manifest_path.exists():
            return json.loads(self.manifest_path.read_text(encoding="utf-8"))
        return {}

    def get_version(self, key: str) -> str | None:
        return self._manifest.get(key, {}).get("version")

    def set_version(self, key: str, version: str | None) -> None:
        self._manifest.setdefault(key, {})["version"] = version

    def save(self) -> None:
        ordered = dict(sorted(self._manifest.items()))
        self.manifest_path.write_text(
            json.dumps(ordered, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
        )
