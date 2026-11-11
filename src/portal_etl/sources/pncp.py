"""Ingestão de contratos do PNCP (Portal Nacional de Contratações Públicas).

A API de consulta é lenta e devolve 500/504 em consultas pesadas (ex.: um ano inteiro de um
órgão grande). Por isso:

- a consulta é feita em **janelas mensais** (data de publicação), que são leves;
- cada mês vira uma partição própria na bronze, então o progresso é salvo mês a mês e uma
  falha num mês não descarta os outros;
- meses já encerrados há mais de 60 dias não são baixados de novo (a menos que `force=True`);
- há um **disjuntor**: após N falhas seguidas o PNCP é abandonado nesta execução, e um
  **orçamento de tempo** encerra a coleta de forma limpa. A próxima execução continua de onde parou.

Documentação: https://pncp.gov.br/api/consulta/swagger-ui/index.html
"""

from __future__ import annotations

import calendar
import logging
import time
from datetime import date, timedelta

from ..bronze import BronzeStore
from ..config import Municipio
from ..http import ApiClient

log = logging.getLogger("portal_etl.pncp")

BASE_URL = "https://pncp.gov.br/api/consulta/v1/contratos"
PAGE_SIZE = 50  # páginas pequenas respondem mais rápido e falham menos
MESES_REABERTOS = 2  # meses recentes sempre re-consultados (publicações atrasadas/retificações)
PAUSA_429 = 60  # segundos de espera quando o PNCP sinaliza excesso de requisições


class PncpIndisponivel(Exception):
    """Disjuntor aberto: falhas consecutivas demais."""


class PncpIngestor:
    def __init__(
        self,
        client: ApiClient,
        store: BronzeStore,
        ano_corrente: int,
        force: bool = False,
        max_falhas_seguidas: int = 4,
        prazo: float | None = None,
        hoje: date | None = None,
    ):
        self.client = client
        self.store = store
        self.ano_corrente = ano_corrente
        self.force = force
        self.max_falhas_seguidas = max_falhas_seguidas
        self.prazo = prazo  # time.monotonic() limite
        self.hoje = hoje or date.today()
        self.falhas_seguidas = 0
        self.summary = {"baixados": 0, "pulados": 0, "linhas": 0, "falhas": 0, "vazios": 0}

    def tempo_esgotado(self) -> bool:
        return self.prazo is not None and time.monotonic() > self.prazo

    def fetch_contratos(self, cnpj: str, inicio: date, fim: date) -> list[dict]:
        contratos: list[dict] = []
        pagina = 1
        while True:
            params = {
                "dataInicial": inicio.strftime("%Y%m%d"),
                "dataFinal": fim.strftime("%Y%m%d"),
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

    def meses(self, ano: int) -> list[tuple[date, date]]:
        """Janelas mensais do ano (até hoje), da mais recente para a mais antiga."""
        out = []
        for mes in range(12, 0, -1):
            inicio = date(ano, mes, 1)
            if inicio > self.hoje:
                continue
            fim = date(ano, mes, calendar.monthrange(ano, mes)[1])
            out.append((inicio, min(fim, self.hoje)))
        return out

    def ingest_mes(self, mun: Municipio, inicio: date, fim: date) -> None:
        parts = {"cod_ibge": mun.cod_ibge, "ano_publicacao": inicio.year, "mes": inicio.month}
        limite_reabertura = self.hoje.replace(day=1) - timedelta(days=31 * MESES_REABERTOS)
        encerrado = fim < limite_reabertura
        if encerrado and not self.force and self.store.exists("pncp", "contratos", parts):
            self.summary["pulados"] += 1
            return
        try:
            contratos = self.fetch_contratos(mun.cnpj, inicio, fim)
        except Exception as exc:  # noqa: BLE001 - registra e segue para o próximo mês
            self.falhas_seguidas += 1
            self.summary["falhas"] += 1
            log.warning("PNCP %s %s falhou: %s", mun.nome, inicio.strftime("%Y-%m"), exc)
            if "429" in str(exc):
                # Limite de requisições: pausa longa antes de seguir (não conta como queda).
                time.sleep(PAUSA_429)
                self.falhas_seguidas -= 1
            if self.falhas_seguidas >= self.max_falhas_seguidas:
                raise PncpIndisponivel(
                    f"{self.falhas_seguidas} falhas seguidas no PNCP; tentando de novo na "
                    "próxima execução"
                ) from exc
            return
        self.falhas_seguidas = 0
        for c in contratos:
            c["cod_ibge"] = mun.cod_ibge  # chave de junção explícita
        # Mês sem contratos também é registrado (arquivo vazio) para não ser re-consultado.
        n = self.store.write("pncp", "contratos", parts, contratos, source_url=BASE_URL)
        self.summary["baixados"] += 1
        self.summary["linhas"] += n
        if not n:
            self.summary["vazios"] += 1

    def ingest_municipio_ano(self, mun: Municipio, ano: int) -> None:
        for inicio, fim in self.meses(ano):
            if self.tempo_esgotado():
                return
            self.ingest_mes(mun, inicio, fim)
