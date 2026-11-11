import httpx
import respx

from portal_etl.bronze import BronzeStore
from portal_etl.config import Municipio
from portal_etl.export import mascarar_documento
from portal_etl.http import ApiClient
from portal_etl.sources.pncp import BASE_URL, PncpIngestor

MUN = Municipio(5221858, "Valparaíso de Goiás", "GO", "01616319000109", "valparaiso")


def test_retry_em_erro_transitorio(monkeypatch):
    monkeypatch.setattr("tenacity.nap.time.sleep", lambda _s: None)
    client = ApiClient(throttle={})
    with respx.mock() as router:
        route = router.get("https://example.gov.br/x")
        route.side_effect = [
            httpx.Response(503),
            httpx.Response(429),
            httpx.Response(200, json={"ok": True}),
        ]
        status, payload = client.get_json("https://example.gov.br/x")
    assert status == 200 and payload == {"ok": True}
    assert route.call_count == 3


def test_204_e_resposta_vazia_valida():
    client = ApiClient(throttle={})
    with respx.mock() as router:
        router.get("https://example.gov.br/vazio").mock(return_value=httpx.Response(204))
        assert client.get_json("https://example.gov.br/vazio") == (204, None)


def test_pncp_pagina_e_marca_municipio(tmp_path):
    store = BronzeStore(tmp_path)
    client = ApiClient(throttle={})
    with respx.mock() as router:
        route = router.get(BASE_URL)
        route.side_effect = [
            httpx.Response(200, json={"data": [{"numeroControlePNCP": "a"}], "totalPaginas": 2}),
            httpx.Response(200, json={"data": [{"numeroControlePNCP": "b"}], "totalPaginas": 2}),
        ]
        ing = PncpIngestor(client, store, ano_corrente=2026)
        ing.ingest_municipio_ano(MUN, 2025)
    assert ing.summary["linhas"] == 2
    assert route.calls[0].request.url.params["cnpjOrgao"] == MUN.cnpj


def test_pncp_nao_rebaixa_ano_encerrado(tmp_path):
    store = BronzeStore(tmp_path)
    store.write(
        "pncp", "contratos", {"cod_ibge": MUN.cod_ibge, "ano_publicacao": 2023}, [{"x": 1}], "u"
    )
    with respx.mock(assert_all_called=False) as router:
        route = router.get(BASE_URL)
        ing = PncpIngestor(ApiClient(throttle={}), store, ano_corrente=2026)
        ing.ingest_municipio_ano(MUN, 2023)
    assert route.call_count == 0 and ing.summary["pulados"] == 1


def test_mascara_cpf_mas_mantem_cnpj():
    assert mascarar_documento("12345678901", "PF") == "***.456.789-**"
    assert mascarar_documento("01616319000109", "PJ") == "01.616.319/0001-09"
    assert mascarar_documento(None, "PJ") is None
