"""Ingestão do SICONFI (Tesouro Nacional) — RREO, RGF e DCA.

Estratégia incremental "orientada a entregas": para cada município/ano consultamos o
`extrato_entregas`, que lista cada relatório homologado/retificado com sua data de status.
Só baixamos um relatório quando ele é novo ou quando a data de status mudou (retificação),
o que reduz centenas de chamadas a poucas dezenas numa execução típica.

Documentação da API: https://apidatalake.tesouro.gov.br/docs/siconfi/
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Any

from ..bronze import BronzeStore
from ..config import Municipio
from ..http import ApiClient

log = logging.getLogger("portal_etl.siconfi")

BASE_URL = "https://apidatalake.tesouro.gov.br/ords/siconfi/tt"

ENTREGA_RREO = "Relatório Resumido de Execução Orçamentária"
ENTREGA_RGF = "Relatório de Gestão Fiscal"
ENTREGA_DCA = "Balanço Anual (DCA)"

ANEXOS_RREO = ("RREO-Anexo 01", "RREO-Anexo 02")
ANEXOS_DCA = ("DCA-Anexo I-E",)
ANEXO_RGF = "RGF-Anexo 01"

_CAMARA = re.compile(r"c[aâ]mara", re.IGNORECASE)


@dataclass(frozen=True)
class Entrega:
    entregavel: str
    periodo: int
    periodicidade: str
    data_status: str


def fetch_paginated(client: ApiClient, endpoint: str, params: dict[str, Any]) -> list[dict]:
    """Percorre a paginação ORDS (`hasMore`/`offset`) e devolve todos os itens."""
    items: list[dict] = []
    offset = 0
    while True:
        page_params = dict(params)
        if offset:
            page_params["offset"] = offset
        _, payload = client.get_json(f"{BASE_URL}/{endpoint}", page_params)
        if not payload:
            break
        batch = payload.get("items", [])
        items.extend(batch)
        if not payload.get("hasMore") or not batch:
            break
        offset += len(batch)
    return items


def parse_extrato(items: list[dict]) -> list[Entrega]:
    """Filtra as entregas do Poder Executivo (exclui a Câmara) e normaliza os campos."""
    out: dict[tuple[str, int, str], Entrega] = {}
    for it in items:
        if _CAMARA.search(it.get("instituicao") or ""):
            continue
        ent = Entrega(
            entregavel=it.get("entregavel", ""),
            periodo=int(it.get("periodo") or 0),
            periodicidade=(it.get("periodicidade") or "").strip(),
            data_status=str(it.get("data_status") or ""),
        )
        key = (ent.entregavel, ent.periodo, ent.periodicidade)
        # Em caso de duplicidade, fica a entrega mais recente.
        if key not in out or ent.data_status > out[key].data_status:
            out[key] = ent
    return list(out.values())


def ultima_entrega(entregas: list[Entrega], entregavel: str) -> Entrega | None:
    candidatas = [e for e in entregas if e.entregavel == entregavel]
    if not candidatas:
        return None
    return max(candidatas, key=lambda e: (e.periodo, e.data_status))


class SiconfiIngestor:
    def __init__(self, client: ApiClient, store: BronzeStore, force: bool = False):
        self.client = client
        self.store = store
        self.force = force
        self.summary = {"baixados": 0, "pulados": 0, "linhas": 0, "vazios": 0}

    # ------------------------------------------------------------------ util
    def _changed(self, key: str, version: str, dataset: str, partitions: dict) -> bool:
        if self.force:
            return True
        same = self.store.get_version(key) == version
        return not (same and self.store.exists("siconfi", dataset, partitions))

    def _save(self, dataset: str, partitions: dict, endpoint: str, params: dict) -> int:
        items = fetch_paginated(self.client, endpoint, params)
        url = f"{BASE_URL}/{endpoint}"
        if not items:
            self.summary["vazios"] += 1
            log.info("sem dados: %s %s", dataset, partitions)
            return 0
        n = self.store.write("siconfi", dataset, partitions, items, source_url=url)
        self.summary["baixados"] += 1
        self.summary["linhas"] += n
        return n

    # ----------------------------------------------------------- relatórios
    def ingest_rreo(self, ente: int, ano: int, periodo: int, version: str) -> None:
        for anexo in ANEXOS_RREO:
            parts = {"anexo": anexo, "cod_ibge": ente, "ano": ano, "periodo": periodo}
            key = f"siconfi|rreo|{ente}|{ano}|{periodo}|{anexo}"
            if not self._changed(key, version, "rreo", parts):
                self.summary["pulados"] += 1
                continue
            params = {
                "an_exercicio": ano,
                "nr_periodo": periodo,
                "co_tipo_demonstrativo": "RREO",
                "no_anexo": anexo,
                "co_esfera": "M",
                "id_ente": ente,
            }
            if self._save("rreo", parts, "rreo", params):
                self.store.set_version(key, version)

    def ingest_rgf(self, ente: int, ano: int, periodo: int, periodicidade: str, version: str):
        parts = {"cod_ibge": ente, "ano": ano, "periodicidade": periodicidade, "periodo": periodo}
        key = f"siconfi|rgf|{ente}|{ano}|{periodicidade}{periodo}"
        if not self._changed(key, version, "rgf", parts):
            self.summary["pulados"] += 1
            return
        params = {
            "an_exercicio": ano,
            "in_periodicidade": periodicidade,
            "nr_periodo": periodo,
            "co_tipo_demonstrativo": "RGF",
            "no_anexo": ANEXO_RGF,
            "co_esfera": "M",
            "co_poder": "E",
            "id_ente": ente,
        }
        if self._save("rgf", parts, "rgf", params):
            self.store.set_version(key, version)

    def ingest_dca(self, ente: int, ano: int, version: str) -> None:
        for anexo in ANEXOS_DCA:
            parts = {"anexo": anexo, "cod_ibge": ente, "ano": ano}
            key = f"siconfi|dca|{ente}|{ano}|{anexo}"
            if not self._changed(key, version, "dca", parts):
                self.summary["pulados"] += 1
                continue
            params = {"an_exercicio": ano, "no_anexo": anexo, "id_ente": ente}
            if self._save("dca", parts, "dca", params):
                self.store.set_version(key, version)

    # -------------------------------------------------------------- orquestra
    def ingest_municipio_ano(self, mun: Municipio, ano: int) -> None:
        extrato = fetch_paginated(
            self.client, "extrato_entregas", {"id_ente": mun.cod_ibge, "an_referencia": ano}
        )
        entregas = parse_extrato(extrato)
        if not entregas:
            log.warning("%s/%s: extrato vazio, tentando relatórios de fechamento", mun.nome, ano)
            self.ingest_rreo(mun.cod_ibge, ano, 6, "sem-extrato")
            self.ingest_rgf(mun.cod_ibge, ano, 3, "Q", "sem-extrato")
            self.ingest_dca(mun.cod_ibge, ano, "sem-extrato")
            return

        if rreo := ultima_entrega(entregas, ENTREGA_RREO):
            self.ingest_rreo(mun.cod_ibge, ano, rreo.periodo, rreo.data_status)
        if rgf := ultima_entrega(entregas, ENTREGA_RGF):
            per = rgf.periodicidade if rgf.periodicidade in ("Q", "S") else "Q"
            self.ingest_rgf(mun.cod_ibge, ano, rgf.periodo, per, rgf.data_status)
        if dca := ultima_entrega(entregas, ENTREGA_DCA):
            self.ingest_dca(mun.cod_ibge, ano, dca.data_status)
