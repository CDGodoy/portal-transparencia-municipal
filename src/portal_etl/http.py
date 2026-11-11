"""Cliente HTTP resiliente: retry com backoff exponencial, throttle por host e logs estruturados.

As APIs públicas brasileiras são instáveis (timeouts, 429, 5xx esporádicos). Toda a ingestão
passa por aqui para garantir o mesmo comportamento e para facilitar testes com `respx`.
"""

from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import urlparse

import httpx
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_random_exponential,
)

log = logging.getLogger("portal_etl.http")

USER_AGENT = (
    "portal-transparencia-municipal/1.0 "
    "(projeto open source de dados abertos; +https://github.com/CDGodoy/portal-transparencia-municipal)"
)

# Intervalo mínimo entre requisições por host (segundos). O SICONFI documenta limite de
# requisições por segundo; o PNCP é lento e sensível a rajadas.
DEFAULT_THROTTLE = {
    "apidatalake.tesouro.gov.br": 1.1,
    "pncp.gov.br": 2.0,
    "api.bcb.gov.br": 0.3,
}


class RetryableHTTPError(Exception):
    """Erro transitório que merece nova tentativa (429/5xx)."""

    def __init__(self, status: int, url: str):
        super().__init__(f"HTTP {status} em {url}")
        self.status = status


def _is_retryable(exc: BaseException) -> bool:
    return isinstance(exc, RetryableHTTPError | httpx.TransportError | httpx.TimeoutException)


@dataclass
class ApiClient:
    timeout: float = 120.0
    max_attempts: int = 6
    throttle: dict[str, float] = field(default_factory=lambda: dict(DEFAULT_THROTTLE))
    _client: httpx.Client | None = None
    _last_call: dict[str, float] = field(default_factory=dict)
    _lock: threading.Lock = field(default_factory=threading.Lock)
    stats: dict[str, int] = field(default_factory=lambda: {"requests": 0, "retries": 0})

    def __post_init__(self) -> None:
        self._client = httpx.Client(
            timeout=httpx.Timeout(self.timeout, connect=30.0),
            headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
            follow_redirects=True,
        )

    def close(self) -> None:
        if self._client:
            self._client.close()

    def __enter__(self) -> ApiClient:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    def _wait_turn(self, url: str) -> None:
        host = urlparse(url).hostname or ""
        interval = self.throttle.get(host, 0.0)
        if not interval:
            return
        with self._lock:
            elapsed = time.monotonic() - self._last_call.get(host, 0.0)
            if elapsed < interval:
                time.sleep(interval - elapsed)
            self._last_call[host] = time.monotonic()

    def get_json(self, url: str, params: dict[str, Any] | None = None) -> tuple[int, Any]:
        """GET com retry. Retorna (status, json|None). 204/404 são respostas válidas sem dados."""

        @retry(
            retry=retry_if_exception(_is_retryable),
            stop=stop_after_attempt(self.max_attempts),
            wait=wait_random_exponential(multiplier=2, max=60),
            before_sleep=before_sleep_log(log, logging.WARNING),
            reraise=True,
        )
        def _do() -> tuple[int, Any]:
            self._wait_turn(url)
            self.stats["requests"] += 1
            assert self._client is not None
            resp = self._client.get(url, params=params)
            if resp.status_code == 429 or resp.status_code >= 500:
                self.stats["retries"] += 1
                raise RetryableHTTPError(resp.status_code, str(resp.url))
            if resp.status_code in (204, 404) or not resp.content:
                return resp.status_code, None
            resp.raise_for_status()
            return resp.status_code, resp.json()

        return _do()
