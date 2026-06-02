from __future__ import annotations

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app.api.dependencies import get_container
from app.api.rest.routes import router as rest_router
from app.api.websocket.stream_endpoint import router as websocket_router
from app.core.capabilities import build_capabilities
from app.core.exceptions import AppError
from app.core.logging import configure_logging

container = get_container()
configure_logging(container.settings.log_level)

app = FastAPI(title=container.settings.app_name, version="0.1.0")


@app.exception_handler(AppError)
async def app_error_handler(_, exc: AppError):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": exc.message}},
    )


@app.get("/health")
async def health() -> dict[str, object]:
    return {
        "status": "ok",
        "service": container.settings.app_name,
        "environment": container.settings.app_env,
    }


@app.get("/capabilities")
async def capabilities() -> dict[str, object]:
    info = build_capabilities(container.settings)
    info["runtime"] = {"registries": container.providers.available()}
    return info


if container.settings.enable_rest:
    app.include_router(rest_router)
if container.settings.enable_websocket:
    app.include_router(websocket_router)
