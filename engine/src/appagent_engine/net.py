"""Network retry and error classification helpers."""

from __future__ import annotations

import socket
import ssl
import time
from collections.abc import Callable
from typing import TypeVar

import httpx

T = TypeVar("T")

RETRYABLE_HTTP_STATUS = {408, 409, 425, 429, 500, 502, 503, 504}


def classify_error(exc: BaseException) -> str:
    """Return a stable error class for health/status reporting."""
    status = _http_status(exc)
    if status is not None:
        if status == 404:
            return "not_found"
        if status in (401, 403):
            return "auth"
        if status in RETRYABLE_HTTP_STATUS:
            return "transient"
        return "http"

    if isinstance(exc, (TimeoutError, socket.timeout, httpx.TimeoutException)):
        return "transient"
    if isinstance(exc, (ssl.SSLError, httpx.NetworkError, httpx.RemoteProtocolError)):
        return "transient"

    text = str(exc).lower()
    if any(token in text for token in ("timeout", "timed out", "ssl", "eof", "temporar")):
        return "transient"
    return "unknown"


def is_retryable_error(exc: BaseException) -> bool:
    return classify_error(exc) == "transient"


def with_retry(
    operation: Callable[[], T],
    *,
    attempts: int = 3,
    base_delay: float = 0.75,
    max_delay: float = 6.0,
    retryable: Callable[[BaseException], bool] = is_retryable_error,
) -> T:
    """Run an operation with exponential backoff for transient failures."""
    last_error: BaseException | None = None
    for attempt in range(1, attempts + 1):
        try:
            return operation()
        except Exception as exc:
            last_error = exc
            if attempt >= attempts or not retryable(exc):
                raise
            delay = min(max_delay, base_delay * (2 ** (attempt - 1)))
            time.sleep(delay)
    raise last_error  # type: ignore[misc]


def retry_httpx_get(
    url: str,
    *,
    attempts: int = 3,
    timeout: float = 30.0,
    follow_redirects: bool = False,
    **kwargs,
) -> httpx.Response:
    """GET a URL using httpx with retryable error handling."""

    def _request() -> httpx.Response:
        with httpx.Client(timeout=timeout, follow_redirects=follow_redirects) as client:
            resp = client.get(url, **kwargs)
            resp.raise_for_status()
            return resp

    return with_retry(_request, attempts=attempts)


def _http_status(exc: BaseException) -> int | None:
    if isinstance(exc, httpx.HTTPStatusError):
        return exc.response.status_code

    # googleapiclient.errors.HttpError exposes resp.status.
    resp = getattr(exc, "resp", None)
    status = getattr(resp, "status", None)
    if isinstance(status, int):
        return status
    try:
        return int(status) if status is not None else None
    except (TypeError, ValueError):
        return None
