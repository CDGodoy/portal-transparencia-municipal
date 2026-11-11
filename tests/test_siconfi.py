import httpx
import respx

from portal_etl.bronze import BronzeStore
from portal_etl.config import Municipio
from portal_etl.http import ApiClient
from portal_etl.sources import siconfi
from portal_etl.sources.siconfi import SiconfiIngestor, parse_extrato, ultima_entrega

MUN = Municipio(5221858, "Valparaíso de Goiás", "GO", "01616319000109", "valparaiso")
PREF = "Prefeitura Municipal de Valparaíso de Goiás - GO"


def _extrato(status_rreo="2025-01-10T00:00:00Z"):
    return {
        "items": [
            {
                "instituicao": PREF,
                "entregavel": siconfi.ENTREGA_RREO,
                "periodo": 5,
                "periodicidade": "B",
                "data_status": "2024-11-29T00:00:00Z",
            },
            {
                "instituicao": PREF,
                "entregavel": siconfi.ENTREGA_RREO,
                "periodo": 6,
                "periodicidade": "B",
                "data_status": status_rreo,
            },
            {
                "instituicao": "Câmara Municipal de Valparaíso de Goiás - GO",
                "entregavel": siconfi.ENTREGA_RGF,
                "periodo": 3,
                "periodicidade": "Q",
                "data_status": "2025-01-30T00:00:00Z",
            },
            {
                "instituicao": PREF,
                "entregavel": siconfi.ENTREGA_RGF,
                "periodo": 2,
                "periodicidade": "Q",
                "data_status": "2024-09-30T00:00:00Z",
            },
            {
                "instituicao": PREF,
                "entregavel": siconfi.ENTREGA_DCA,
                "periodo": 1,
                "periodicidade": "A",
                "data_status": "2025-04-30T00:00:00Z",
            },
        ],
        "hasMore": False,
    }


def test_parse_extrato_ignora_camara_e_pega_ultimo_periodo():
    entregas = parse_extrato(_extrato()["items"])
    rgf = ultima_entrega(entregas, siconfi.ENTREGA_RGF)
    assert rgf.periodo == 2  # o RGF 3 é da Câmara, não do Executivo
    assert ultima_entrega(entregas, siconfi.ENTREGA_RREO).periodo == 6


def _mock_api(router, extrato):
    base = siconfi.BASE_URL
    router.get(f"{base}/extrato_entregas").mock(return_value=httpx.Response(200, json=extrato))
    item = {"exercicio": 2024, "cod_ibge": MUN.cod_ibge, "valor": 1.0, "coluna": "x"}
    rreo = router.get(f"{base}/rreo").mock(
        return_value=httpx.Response(200, json={"items": [item], "hasMore": False})
    )
    rgf = router.get(f"{base}/rgf").mock(
        return_value=httpx.Response(200, json={"items": [item], "hasMore": False})
    )
    dca = router.get(f"{base}/dca").mock(
        return_value=httpx.Response(200, json={"items": [item], "hasMore": False})
    )
    return rreo, rgf, dca


def test_ingestao_incremental_so_rebaixa_quando_ha_retificacao(tmp_path):
    store = BronzeStore(tmp_path)
    client = ApiClient(throttle={})
    with respx.mock(assert_all_called=False) as router:
        rreo, rgf, dca = _mock_api(router, _extrato())
        SiconfiIngestor(client, store).ingest_municipio_ano(MUN, 2024)
        assert rreo.call_count == 2  # anexos 01 e 02
        assert rgf.call_count == 1 and dca.call_count == 1
        assert rgf.calls[0].request.url.params["nr_periodo"] == "2"

    # Segunda execução sem mudanças: nada é baixado.
    with respx.mock(assert_all_called=False) as router:
        rreo, rgf, dca = _mock_api(router, _extrato())
        ing = SiconfiIngestor(client, store)
        ing.ingest_municipio_ano(MUN, 2024)
        assert rreo.call_count == rgf.call_count == dca.call_count == 0
        assert ing.summary["pulados"] == 4

    # RREO retificado (nova data de status): só o RREO é baixado de novo.
    with respx.mock(assert_all_called=False) as router:
        rreo, rgf, dca = _mock_api(router, _extrato(status_rreo="2025-09-29T19:48:32Z"))
        SiconfiIngestor(client, store).ingest_municipio_ano(MUN, 2024)
        assert rreo.call_count == 2 and rgf.call_count == 0 and dca.call_count == 0


def test_paginacao_ords(tmp_path):
    client = ApiClient(throttle={})
    with respx.mock() as router:
        route = router.get(f"{siconfi.BASE_URL}/rreo")
        route.side_effect = [
            httpx.Response(200, json={"items": [{"i": 1}, {"i": 2}], "hasMore": True}),
            httpx.Response(200, json={"items": [{"i": 3}], "hasMore": False}),
        ]
        items = siconfi.fetch_paginated(client, "rreo", {"id_ente": 1})
    assert [i["i"] for i in items] == [1, 2, 3]
    assert route.calls[1].request.url.params["offset"] == "2"
