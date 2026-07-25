from time import perf_counter

from fastapi import Request, Response
from prometheus_client import Counter, Histogram

REQUEST_COUNT = Counter(
    "orders_http_requests_total",
    "Total HTTP requests processed by the orders service",
    ["method", "path", "status"],
)
REQUEST_DURATION = Histogram(
    "orders_http_request_duration_seconds",
    "Orders service HTTP request duration",
    ["method", "path"],
)
ORDER_COUNT = Counter(
    "orders_created_total",
    "Total number of confirmed orders",
)


async def metrics_middleware(request: Request, call_next) -> Response:
    started_at = perf_counter()
    response = await call_next(request)
    path = request.url.path
    REQUEST_COUNT.labels(request.method, path, str(response.status_code)).inc()
    REQUEST_DURATION.labels(request.method, path).observe(perf_counter() - started_at)
    response.headers["X-Service-Name"] = "orders-service"
    return response
