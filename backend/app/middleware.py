from __future__ import annotations

import uuid
from fastapi import Request
from time import perf_counter
from loguru import logger


async def correlation_id_middleware(request: Request, call_next):
    correlation_id = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())
    request.state.correlation_id = correlation_id
    response = await call_next(request)
    response.headers["X-Correlation-ID"] = correlation_id
    return response


async def request_logging_middleware(request: Request, call_next):
    start = perf_counter()
    response = await call_next(request)
    duration_ms = (perf_counter() - start) * 1000
    logger.bind(
        method=request.method,
        path=str(request.url.path),
        status=response.status_code,
        durationMs=round(duration_ms, 2),
        principal=getattr(request.state, "principal", None),
        correlationId=getattr(request.state, "correlation_id", None),
    ).info("http.request")
    return response





