"""Ingestão de contratos do PNCP (Portal Nacional de Contratações Públicas).

Consulta pública por CNPJ do órgão e janela de data de publicação. A API é lenta e
instável, então usamos páginas pequenas e o cliente com retry. Anos já encerrados
(anteriores ao ano passado) não são baixados novamente, a menos que `force=True`.

Documentação: https://pncp.gov.br/api/consulta/swagger-ui/index.html
"""

from __future__ import annotations

import logging

from ..bronze import BronzeStore
from ..config import Municipio
from ..http import ApiClient

log = logging.getLogger("portal_etl.pncp")

BASE_URL = "https://pncp.gov.br/api/consulta/v1/contratos"
PAGE_SIZE = 100  # a API recusa > 500 e fica instável com páginas grandes


class PncpIngestor:
    def __init__(self, client: ApiClient, store: BronzeStore, ano_corrente: int, force=False):
        self.client = client
        self.store = store
        self.ano_corrente = ano_corrente
        self.force = force
        self.summary = {"baixados": 0, "pulados": 0, "linhas": 0}

    def fetch_contratos(self, cnpj: str, ano: int) -> list[dict]:
        contratos: list[dict] = []
        pagina = 1
        while True:
            params = {
                "dataInicial": f"{ano}0101",
                "dataFinal": f"{ano}1231",
                "cnpjOrgao": cnpj,
                "pagina": pagina,
                "tamanhoPagina": PAGE_SIZE,
            }
            _, payload = self.client.get_json(BASE_URL, params)
            if not payload:
                break
            contratos.extend(payload.get("data") or [])
            if pagina >= int(payload.get("totalPaginas") or 1):
                break
            pagina += 1
        return contratos

    def ingest_municipio_ano(self, mun: Municipio, ano: int) -> None:
        parts = {"cod_ibge": mun.cod_ibge, "ano_publicacao": ano}
        encerrado = ano < self.ano_corrente - 1
        if encerrado and not self.force and self.store.exists("pncp", "contratos", parts):
            self.summary["pulados"] += 1
            return
        contratos = self.fetch_contratos(mun.cnpj, ano)
        for c in contratos:
            c["cod_ibge"] = mun.cod_ibge  # chave de junção explícita
        if not contratos:
            log.info("PNCP sem contratos: %s %s", mun.nome, ano)
            return
        n = self.store.write("pncp", "contratos", parts, contratos, source_url=BASE_URL)
        self.summary["baixados"] += 1
        self.summary["linhas"] += n
