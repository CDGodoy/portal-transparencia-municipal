import gzip
import json

from portal_etl.bronze import BronzeStore


def test_write_is_idempotent_and_deterministic(tmp_path):
    store = BronzeStore(tmp_path)
    parts = {"cod_ibge": 1, "ano": 2024}
    store.write("src", "ds", parts, [{"a": 1}, {"a": 2}], "http://x")
    path = store.path_for("src", "ds", parts)
    first = path.read_bytes()
    store.write("src", "ds", parts, [{"a": 1}, {"a": 2}], "http://x")
    assert path.read_bytes() == first  # mesmo conteúdo => mesmo arquivo (diff limpo no git)

    lines = [json.loads(x) for x in gzip.decompress(first).decode().splitlines()]
    assert [r["_ordem"] for r in lines] == [0, 1]
    assert all(r["_source_url"] == "http://x" for r in lines)


def test_partition_path_is_hive_style(tmp_path):
    store = BronzeStore(tmp_path)
    p = store.path_for("siconfi", "rreo", {"anexo": "RREO-Anexo 01", "ano": 2024})
    assert (
        p.relative_to(tmp_path).as_posix()
        == "siconfi/rreo/anexo=RREO-Anexo_01/ano=2024/data.ndjson.gz"
    )


def test_manifest_roundtrip(tmp_path):
    store = BronzeStore(tmp_path)
    store.set_version("k", "2025-01-01")
    store.save()
    assert BronzeStore(tmp_path).get_version("k") == "2025-01-01"
