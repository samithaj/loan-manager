from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from loguru import logger


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):  # type: ignore[override]
        correlation_id = getattr(request.state, "correlation_id", None)
        logger.bind(route=str(getattr(request.scope, 'path', '')), correlationId=correlation_id).exception("unhandled exception")
        return JSONResponse(
            status_code=500,
            content={
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred",
                "correlationId": correlation_id,
            },
        )





