import time

from fastapi import Request, Response
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Histogram,
    generate_latest,
)

REQUEST_COUNT = Counter(
    "datheon_http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
)

REQUEST_LATENCY = Histogram(
    "datheon_http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
)

REQUEST_ERRORS = Counter(
    "datheon_http_errors_total",
    "Total HTTP errors",
    ["method", "endpoint", "status"],
)


def install_metrics(app):
    @app.middleware("http")
    async def metrics_middleware(request: Request, call_next):
        if request.url.path == "/metrics":
            return await call_next(request)

        method = request.method
        start_time = time.perf_counter()

        try:
            response = await call_next(request)
        except Exception:
            duration = time.perf_counter() - start_time
            route = request.scope.get("route")
            endpoint = getattr(route, "path", request.url.path)

            REQUEST_COUNT.labels(method, endpoint, "500").inc()
            REQUEST_ERRORS.labels(method, endpoint, "500").inc()
            REQUEST_LATENCY.labels(method, endpoint).observe(duration)
            raise

        duration = time.perf_counter() - start_time
        route = request.scope.get("route")
        endpoint = getattr(route, "path", request.url.path)
        status = str(response.status_code)

        REQUEST_COUNT.labels(method, endpoint, status).inc()
        REQUEST_LATENCY.labels(method, endpoint).observe(duration)

        if response.status_code >= 400:
            REQUEST_ERRORS.labels(method, endpoint, status).inc()

        return response

    @app.get("/metrics", include_in_schema=False)
    async def prometheus_metrics():
        return Response(
            content=generate_latest(),
            media_type=CONTENT_TYPE_LATEST,
        )


LLM_TOKEN_COUNT = Counter(
    "datheon_llm_tokens_total",
    "Total tokens processed by local LLMs",
    ["model", "token_type"],
)


def record_token_usage(model, prompt_tokens, completion_tokens):
    usage = {
        "prompt": prompt_tokens,
        "completion": completion_tokens,
    }

    for token_type, count in usage.items():
        if isinstance(count, int) and count > 0:
            LLM_TOKEN_COUNT.labels(
                model=model,
                token_type=token_type,
            ).inc(count)
