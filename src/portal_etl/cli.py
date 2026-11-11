"""CLI do pipeline: `portal ingest`, `portal transform`, `portal export`, `portal run`."""

from __future__ import annotations

import json
import logging
import sys
import time
from typing import Annotated

import typer

from . import config
from .bronze import BronzeStore
from .http import ApiClient
from .sources.bcb import ingest_ipca
from .sources.pncp import PncpIndisponivel, PncpIngestor
from .sources.siconfi import SiconfiIngestor

app = typer.Typer(help="Pipeline do Portal de Transparência Municipal", no_args_is_help=True)
log = logging.getLogger("portal_etl")


def _setup_logging(verbose: bool) -> None:
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s %(levelname)-7s %(name)s | %(message)s",
        datefmt="%H:%M:%S",
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)


def _selecionar(municipio: list[int] | None):
    todos = config.carregar_municipios()
    if not municipio:
        return todos
    sel = tuple(m for m in todos if m.cod_ibge in set(municipio))
    if not sel:
        raise typer.BadParameter(f"Nenhum município configurado com códigos {municipio}")
    return sel


@app.command()
def ingest(
    fontes: Annotated[str, typer.Option(help="Fontes separadas por vírgula")] = "siconfi,pncp,bcb",
    municipio: Annotated[list[int] | None, typer.Option(help="Código IBGE (repetível)")] = None,
    ano_inicial: Annotated[int, typer.Option()] = config.ANO_INICIAL,
    force: Annotated[bool, typer.Option(help="Ignora o manifesto e baixa tudo")] = False,
    tempo_max_pncp: Annotated[
        float, typer.Option(help="Orçamento de tempo do PNCP em minutos (0 = sem limite)")
    ] = 0,
    verbose: Annotated[bool, typer.Option("--verbose", "-v")] = False,
) -> None:
    """Extrai dados das APIs públicas para a camada bronze (incremental)."""
    _setup_logging(verbose)
    fontes_sel = {f.strip() for f in fontes.split(",") if f.strip()}
    municipios = _selecionar(municipio)
    ano_atual = config.ano_corrente()
    store = BronzeStore(config.BRONZE_DIR)
    falhas: list[str] = []
    t0 = time.monotonic()

    with ApiClient() as client:
        if "bcb" in fontes_sel:
            try:
                n = ingest_ipca(client, store, ano_inicial)
                log.info("IPCA: %s meses", n)
            except Exception as exc:  # noqa: BLE001 - degradação graciosa
                falhas.append(f"bcb/ipca: {exc}")
                log.error("Falha no IPCA: %s", exc)

        if "siconfi" in fontes_sel:
            sic = SiconfiIngestor(client, store, force=force)
            for mun in municipios:
                for ano in range(ano_inicial, ano_atual + 1):
                    try:
                        sic.ingest_municipio_ano(mun, ano)
                    except Exception as exc:  # noqa: BLE001
                        falhas.append(f"siconfi/{mun.cod_ibge}/{ano}: {exc}")
                        log.error("SICONFI %s %s falhou: %s", mun.nome, ano, exc)
                store.save()  # checkpoint por município
            log.info("SICONFI: %s", sic.summary)

        if "pncp" in fontes_sel:
            prazo = time.monotonic() + tempo_max_pncp * 60 if tempo_max_pncp else None
            # O PNCP falha com frequência: menos tentativas por chamada e disjuntor por execução.
            with ApiClient(max_attempts=3) as pncp_client:
                pn = PncpIngestor(
                    pncp_client, store, ano_corrente=ano_atual, force=force, prazo=prazo
                )
                anos = range(ano_atual, max(ano_inicial, config.ANO_INICIAL_PNCP) - 1, -1)
                try:
                    for mun in municipios:
                        for ano in anos:  # mais recente primeiro
                            if pn.tempo_esgotado():
                                break
                            pn.ingest_municipio_ano(mun, ano)
                        store.save()
                except PncpIndisponivel as exc:
                    falhas.append(f"pncp: {exc}")
                    log.error("%s", exc)
                if pn.tempo_esgotado():
                    log.warning(
                        "Orçamento de tempo do PNCP esgotado; continua na próxima execução."
                    )
                client.stats["requests"] += pncp_client.stats["requests"]
                client.stats["retries"] += pncp_client.stats["retries"]
            log.info("PNCP: %s", pn.summary)

        store.save()
        log.info(
            "Ingestão concluída em %.0fs (%s requisições, %s retries, %s falhas)",
            time.monotonic() - t0,
            client.stats["requests"],
            client.stats["retries"],
            len(falhas),
        )

    report = {"falhas": falhas, "requisicoes": client.stats}
    (config.DATA_DIR / "ingest_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8"
    )
    # Falhas parciais não derrubam o pipeline (os dados anteriores continuam válidos);
    # só falhamos se nada funcionou.
    if falhas and client.stats["requests"] <= len(falhas):
        log.error("Todas as requisições falharam — abortando.")
        raise typer.Exit(code=1)


@app.command()
def transform(
    select: Annotated[str | None, typer.Option(help="Seleção dbt (opcional)")] = None,
) -> None:
    """Executa `dbt build` (seeds, modelos e testes de qualidade) no DuckDB."""
    from .transform import run_dbt

    _setup_logging(False)
    args = ["build"] + (["--select", select] if select else [])
    if not run_dbt(args):
        raise typer.Exit(code=1)


@app.command()
def export() -> None:
    """Exporta a camada gold para JSON estático consumido pelo site."""
    from .export import export_all

    _setup_logging(False)
    files = export_all()
    log.info("Exportados %s arquivos para %s", len(files), config.SITE_DATA_DIR)


@app.command()
def run(
    skip_ingest: Annotated[bool, typer.Option(help="Usa apenas a bronze existente")] = False,
) -> None:
    """Pipeline completo: ingest → transform → export."""
    if not skip_ingest:
        ingest(
            fontes="siconfi,pncp,bcb",
            municipio=None,
            ano_inicial=config.ANO_INICIAL,
            force=False,
            verbose=False,
        )
    transform(select=None)
    export()


def main() -> None:  # pragma: no cover
    sys.exit(app())


if __name__ == "__main__":  # pragma: no cover
    main()
