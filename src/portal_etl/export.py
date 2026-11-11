"""Exporta a camada gold (DuckDB) para arquivos JSON estáticos consumidos pelo site.

Um arquivo por município (carregado sob demanda) + índices pequenos. Isso mantém o site
100% estático (GitHub Pages), sem backend nem banco em produção.
"""

from __future__ import annotations

import json
import logging
import math
import re
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

import duckdb

from . import __version__, config

log = logging.getLogger("portal_etl.export")

MAX_CONTRATOS_LISTA = 400
TOP_FORNECEDORES = 15


def _clean(value: Any) -> Any:
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return None
        return round(value, 2)
    if isinstance(value, datetime | date):
        return value.isoformat()
    return value


def _rows(con: duckdb.DuckDBPyConnection, sql: str, params: list | None = None) -> list[dict]:
    cur = con.execute(sql, params or [])
    cols = [d[0] for d in cur.description]
    return [{c: _clean(v) for c, v in zip(cols, row, strict=True)} for row in cur.fetchall()]


def mascarar_documento(doc: str | None, tipo_pessoa: str | None) -> str | None:
    """CPF de pessoa física é mascarado (LGPD); CNPJ é público e fica completo."""
    if not doc:
        return None
    digits = re.sub(r"\D", "", doc)
    if (tipo_pessoa or "").upper() == "PF" or len(digits) == 11:
        return f"***.{digits[3:6]}.{digits[6:9]}-**" if len(digits) == 11 else "***"
    if len(digits) == 14:
        return f"{digits[:2]}.{digits[2:5]}.{digits[5:8]}/{digits[8:12]}-{digits[12:]}"
    return digits


_CPF_NO_NOME = re.compile(r"(?<!\d)(\d{3})\.?(\d{3})\.?(\d{3})-?(\d{2})(?!\d)")


def mascarar_nome(nome: str | None) -> str | None:
    """Razão social de MEI costuma terminar com o CPF do titular; mascaramos esse trecho."""
    if not nome:
        return nome
    return _CPF_NO_NOME.sub(lambda m: f"***.{m.group(2)}.{m.group(3)}-**", nome)


def _write(path: Path, payload: Any) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8"
    )
    return path


def _contratos(con, cod: int) -> dict:
    resumo = _rows(
        con,
        """
        select ano, count(*) as n, sum(valor_global) as valor, sum(valor_global_real) as valor_real
        from gold.fct_contratos where cod_ibge = ? group by ano order by ano
    """,
        [cod],
    )
    categorias = _rows(
        con,
        """
        select ano, categoria, count(*) as n, sum(valor_global) as valor
        from gold.fct_contratos where cod_ibge = ? group by all order by ano, valor desc
    """,
        [cod],
    )
    fornecedores = _rows(
        con,
        f"""
        with agg as (
            select ano, fornecedor_documento as documento, max(fornecedor_tipo_pessoa) as tipo,
                   max(fornecedor_nome) as nome, count(*) as n, sum(valor_global) as valor
            from gold.fct_contratos where cod_ibge = ?
            group by grouping sets ((ano, fornecedor_documento), (fornecedor_documento))
        )
        select * from agg
        qualify row_number() over (partition by ano order by valor desc) <= {TOP_FORNECEDORES}
        order by ano nulls first, valor desc
    """,
        [cod],
    )
    for f in fornecedores:
        f["documento"] = mascarar_documento(f["documento"], f.pop("tipo"))
        f["nome"] = mascarar_nome(f["nome"])
    lista = _rows(
        con,
        f"""
        select numero_controle_pncp as id, data_assinatura as data, ano,
               fornecedor_nome as fornecedor, fornecedor_documento as documento,
               fornecedor_tipo_pessoa as tipo, categoria,
               left(objeto, 240) as objeto, valor_global as valor, unidade_nome as unidade
        from gold.fct_contratos where cod_ibge = ?
        order by data_assinatura desc nulls last, valor_global desc
        limit {MAX_CONTRATOS_LISTA}
    """,
        [cod],
    )
    for c in lista:
        c["documento"] = mascarar_documento(c["documento"], c.pop("tipo"))
        c["fornecedor"] = mascarar_nome(c["fornecedor"])
    return {
        "resumo": resumo,
        "categorias": categorias,
        "fornecedores": fornecedores,
        "lista": lista,
    }


def _municipio(con, mun: dict) -> dict:
    cod = mun["cod_ibge"]
    return {
        **mun,
        "execucao": _rows(
            con,
            """
            select ano, bimestre_referencia as bimestre, exercicio_completo as completo,
                   populacao, receita_prevista_inicial, receita_prevista_atualizada,
                   receita_realizada, dotacao_inicial, dotacao_atualizada, despesa_empenhada,
                   despesa_liquidada, despesa_paga, resultado_orcamentario, fator_real,
                   receita_realizada_real, despesa_liquidada_real,
                   receita_per_capita_real, despesa_per_capita_real
            from gold.fct_execucao_anual where cod_ibge = ? order by ano
        """,
            [cod],
        ),
        "receitas": _rows(
            con,
            """
            select ano, categoria, grupo, ordem, receita_realizada as realizado,
                   receita_prevista as previsto, receita_realizada_real as realizado_real
            from gold.fct_receita_origem where cod_ibge = ? order by ano, ordem, categoria
        """,
            [cod],
        ),
        "natureza": _rows(
            con,
            """
            select ano, grupo_natureza as grupo, ordem, dotacao_atualizada as dotacao,
                   despesa_liquidada as liquidado, despesa_liquidada_real as liquidado_real
            from gold.fct_despesa_natureza where cod_ibge = ? order by ano, ordem
        """,
            [cod],
        ),
        "funcoes": _rows(
            con,
            """
            select ano, nivel, funcao_cod, funcao_nome as funcao, subfuncao_cod,
                   subfuncao_nome as subfuncao, despesa_empenhada as empenhado,
                   despesa_liquidada as liquidado, despesa_paga as pago,
                   despesa_liquidada_real as liquidado_real, fonte
            from gold.fct_despesa_funcao where cod_ibge = ?
            order by ano, funcao_cod, nivel, subfuncao_cod
        """,
            [cod],
        ),
        "pessoal": _rows(
            con,
            """
            select ano, periodicidade, periodo, dtp, rcl, dtp_pct_rcl as pct,
                   limite_maximo_pct as limite_maximo, limite_prudencial_pct as limite_prudencial,
                   limite_alerta_pct as limite_alerta, situacao
            from gold.fct_pessoal_lrf where cod_ibge = ? order by ano, periodo
        """,
            [cod],
        ),
        "contratos": _contratos(con, cod),
        "qualidade": _rows(
            con,
            """
            select ano, severidade, regra, descricao
            from gold.mart_qualidade_dados where cod_ibge = ? order by ano, regra
        """,
            [cod],
        ),
    }


def _ultima_ingestao() -> str | None:
    manifest = config.BRONZE_DIR / "_manifest.json"
    if not manifest.exists():
        return None
    data = json.loads(manifest.read_text(encoding="utf-8"))
    datas = [v.get("ingested_at") for v in data.values() if v.get("ingested_at")]
    return max(datas) if datas else None


def _resultado_testes() -> dict | None:
    rr = config.DBT_DIR / "target" / "run_results.json"
    if not rr.exists():
        return None
    results = json.loads(rr.read_text(encoding="utf-8")).get("results", [])
    testes = [r for r in results if r.get("unique_id", "").startswith("test.")]
    if not testes:
        return None
    contagem: dict[str, int] = {}
    for t in testes:
        contagem[t["status"]] = contagem.get(t["status"], 0) + 1
    return {"total": len(testes), **contagem}


def export_all(db_path: Path | None = None, out_dir: Path | None = None) -> list[Path]:
    db_path = db_path or config.WAREHOUSE_PATH
    out_dir = out_dir or config.SITE_DATA_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []

    with duckdb.connect(str(db_path)) as con:
        municipios = _rows(
            con,
            """
            select m.cod_ibge, m.nome, m.uf, m.slug, m.destaque, m.populacao_recente as populacao,
                   list(e.ano order by e.ano) filter (where e.ano is not null) as anos
            from gold.dim_municipio m
            left join gold.fct_execucao_anual e using (cod_ibge)
            group by all
            order by m.destaque desc, m.nome
        """,
        )
        for m in municipios:
            m["anos"] = m["anos"] or []
        written.append(_write(out_dir / "municipios.json", municipios))

        for mun in municipios:
            if not mun["anos"]:
                continue
            payload = _municipio(con, mun)
            written.append(_write(out_dir / "municipios" / f"{mun['cod_ibge']}.json", payload))

        indicadores = _rows(
            con,
            """
            select i.*, m.nome
            from gold.mart_indicadores i join gold.dim_municipio m using (cod_ibge)
            order by i.ano, m.nome
        """,
        )
        written.append(_write(out_dir / "comparativo.json", indicadores))

        ipca = _rows(con, "select max(mes_referencia) as mes from intermediate.int_ipca__fatores")
        qualidade = _rows(con, "select * from gold.mart_qualidade_dados")
        meta = {
            "versao": __version__,
            "gerado_em": datetime.now(UTC).isoformat(timespec="seconds"),
            "ultima_ingestao": _ultima_ingestao(),
            "ipca_referencia": ipca[0]["mes"] if ipca else None,
            "testes": _resultado_testes(),
            "total_achados_qualidade": len(qualidade),
            "fontes": [
                {
                    "nome": "SICONFI — Tesouro Nacional",
                    "itens": "RREO, RGF e DCA",
                    "url": "https://apidatalake.tesouro.gov.br/docs/siconfi/",
                },
                {
                    "nome": "PNCP — Portal Nacional de Contratações Públicas",
                    "itens": "Contratos",
                    "url": "https://pncp.gov.br/api/consulta/swagger-ui/index.html",
                },
                {
                    "nome": "Banco Central — SGS 433",
                    "itens": "IPCA mensal",
                    "url": "https://dadosabertos.bcb.gov.br/dataset/433-indice-nacional-de-precos-ao-consumidor-amplo-ipca",
                },
            ],
        }
        written.append(_write(out_dir / "meta.json", meta))

    log.info("Exportação concluída: %s arquivos", len(written))
    return written
