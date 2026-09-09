import json
import logging
import os
import re
import sys
import time
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from uuid import uuid4

from starlette.requests import Request
from starlette.responses import Response

from backend.app.metrics import request_route


REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9._-]{1,128}$")
PROBE_PATHS = {"/health", "/ready", "/metrics"}


def configure_access_logger() -> logging.Logger:
    logger = logging.getLogger("reservoir.access")
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter("%(message)s"))
        logger.addHandler(handler)
    logger.setLevel(os.getenv("LOG_LEVEL", "INFO").upper())
    logger.propagate = False
    return logger


access_logger = configure_access_logger()


def request_id_from_header(value: str | None) -> str:
    if value and REQUEST_ID_PATTERN.fullmatch(value):
        return value
    return uuid4().hex


async def log_http_request(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    request_id = request_id_from_header(request.headers.get("X-Request-ID"))
    request.state.request_id = request_id
    started_at = time.perf_counter()
    status_code = 500

    try:
        response = await call_next(request)
        status_code = response.status_code
    except Exception:
        _write_access_log(request, request_id, status_code, started_at)
        raise

    response.headers["X-Request-ID"] = request_id
    _write_access_log(request, request_id, status_code, started_at)
    return response


def _write_access_log(
    request: Request,
    request_id: str,
    status_code: int,
    started_at: float,
) -> None:
    if request.url.path.rstrip("/") in PROBE_PATHS:
        return

    access_logger.info(
        json.dumps(
            {
                "timestamp": datetime.now(UTC).isoformat(),
                "event": "http_request",
                "request_id": request_id,
                "method": request.method,
                "route": request_route(request),
                "status": status_code,
                "duration_ms": round((time.perf_counter() - started_at) * 1000, 2),
            },
            separators=(",", ":"),
        )
    )
