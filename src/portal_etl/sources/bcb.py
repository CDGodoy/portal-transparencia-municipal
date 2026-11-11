"""Série do IPCA (variação % mensal, SGS 433) do Banco Central, usada para deflacionar
valores nominais e permitir comparações em reais constantes."""

from __future__ import annotations

from ..bronze import BronzeStore
from ..http import ApiClient

SERIE_IPCA = 433
URL = f"https://api.bcb.gov.br/dados/serie/bcdata.sgs.{SERIE_IPCA}/dados"


def ingest_ipca(client: ApiClient, store: BronzeStore, ano_inicial: int) -> int:
    params = {"formato": "json", "dataInicial": f"01/01/{ano_inicial - 1}"}
    _, payload = client.get_json(URL, params)
    if not payload:
        return 0
    return store.write("bcb", "ipca", {"serie": SERIE_IPCA}, payload, source_url=URL)
