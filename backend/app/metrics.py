import time
from collections.abc import Awaitable, Callable

from prometheus_client import Counter, Histogram, make_asgi_app
from starlette.requests import Request
from starlette.responses import Response


HTTP_REQUESTS = Counter(
    "reservoir_http_requests_total",
    "Total HTTP requests handled by Reservoir.",
    ("method", "route", "status"),
)
HTTP_REQUEST_DURATION = Histogram(
    "reservoir_http_request_duration_seconds",
    "Reservoir HTTP request duration in seconds.",
    ("method", "route"),
)

metrics_app = make_asgi_app()


def request_route(request: Request) -> str:
    route = request.scope.get("route")
    return getattr(route, "path", "unmatched")


async def record_http_metrics(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    if request.url.path.rstrip("/") == "/metrics":
        return await call_next(request)

    started_at = time.perf_counter()
    status_code = 500

    try:
        response = await call_next(request)
        status_code = response.status_code
        return response
    finally:
        route = request_route(request)
        HTTP_REQUESTS.labels(request.method, route, str(status_code)).inc()
        HTTP_REQUEST_DURATION.labels(request.method, route).observe(
            time.perf_counter() - started_at
        )
