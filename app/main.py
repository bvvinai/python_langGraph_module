from __future__ import annotations

from uuid import uuid4

import structlog
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.exceptions import AppError
from app.core.logging import configure_logging

logger = structlog.get_logger(__name__)


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level)

    app = FastAPI(title=settings.app_name)

    @app.middleware("http")
    async def request_context_middleware(request: Request, call_next):
        trace_id = request.headers.get("x-trace-id") or str(uuid4())
        bound_logger = logger.bind(trace_id=trace_id, path=str(request.url.path), method=request.method)
        bound_logger.info("request_started")
        response = await call_next(request)
        response.headers["x-trace-id"] = trace_id
        bound_logger.info("request_finished", status_code=response.status_code)
        return response

    @app.exception_handler(AppError)
    async def app_error_handler(_: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(status_code=400, content={"error": exc.code, "message": exc.message})

    @app.exception_handler(Exception)
    async def unhandled_error_handler(_: Request, exc: Exception) -> JSONResponse:
        logger.exception("unhandled_error", error=str(exc))
        return JSONResponse(status_code=500, content={"error": "internal_server_error"})

    app.include_router(api_router, prefix="/v1")
    return app


app = create_app()
