"""Teste ponta a ponta: bronze de amostra -> dbt build (modelos + testes) -> export JSON."""

import json
import os

import duckdb
import pytest
import sample_bronze


@pytest.fixture(scope="module")
def pipeline(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("e2e")
    bronze = sample_bronze.build(tmp / "bronze")
    db = tmp / "portal.duckdb"
    out = tmp / "site"
    env = {"PORTAL_BRONZE_DIR": str(bronze), "PORTAL_DUCKDB_PATH": str(db)}
    old = {k: os.environ.get(k) for k in env}
    os.environ.update(env)
    try:
        from portal_etl.export import export_all
        from portal_etl.transform import run_dbt

        assert run_dbt(["build"]), "dbt build falhou (modelo ou teste de qualidade)"
        export_all(db_path=db, out_dir=out)
    finally:
        for k, v in old.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
    return duckdb.connect(str(db)), out


def q(con, sql):
    return con.execute(sql).fetchall()


def test_usa_bimestre_mais_recente(pipeline):
    con, _ = pipeline
    ((b, rec),) = q(
        con,
        "select bimestre_referencia, receita_realizada from gold.fct_execucao_anual "
        "where cod_ibge=5221858 and ano=2026",
    )
    assert b == 4 and rec == 560_000_000


def test_categorias_de_receita_cobrem_layouts_antigo_e_novo(pipeline):
    con, _ = pipeline
    cats_2016 = {
        r[0]
        for r in q(
            con, "select categoria from gold.fct_receita_origem where cod_ibge=5221858 and ano=2016"
        )
    }
    cats_2024 = {
        r[0]
        for r in q(
            con, "select categoria from gold.fct_receita_origem where cod_ibge=5221858 and ano=2024"
        )
    }
    assert "Transferências intergovernamentais (layout até 2017)" in cats_2016
    assert "FUNDEB e outras instituições públicas" in cats_2024


def test_dca_descarta_bloco_intra_orcamentario(pipeline):
    con, _ = pipeline
    rows = q(
        con,
        "select funcao_cod from gold.fct_despesa_funcao "
        "where cod_ibge=5221858 and ano=2024 and nivel='funcao'",
    )
    assert ("09",) not in rows  # a Previdência só aparece no bloco intra da amostra


def test_ano_corrente_usa_rreo_anexo02(pipeline):
    con, _ = pipeline
    rows = dict(
        q(
            con,
            "select funcao_cod, despesa_liquidada from gold.fct_despesa_funcao "
            "where cod_ibge=5221858 and ano=2026",
        )
    )
    assert rows["10"] == 115_000_000 and rows["12"] == 185_000_000


def test_contrato_retificado_deduplicado(pipeline):
    con, _ = pipeline
    ((n, valor),) = q(
        con,
        "select count(*), max(valor_global) from gold.fct_contratos "
        "where fornecedor_nome like 'LEAO%'",
    )
    assert n == 1 and valor == 300_000


def test_achados_de_qualidade(pipeline):
    con, _ = pipeline
    regras = {
        r[0] for r in q(con, "select regra from gold.mart_qualidade_dados where cod_ibge=5221858")
    }
    assert "limite_lrf_inconsistente" in regras  # RGF 2016 declarou limite de 60%


def test_export_gera_arquivos(pipeline):
    _, out = pipeline
    muni = json.loads((out / "municipios" / "5221858.json").read_text())
    assert {"execucao", "receitas", "funcoes", "pessoal", "contratos", "qualidade"} <= set(muni)
    assert json.loads((out / "meta.json").read_text())["testes"]["total"] > 30
