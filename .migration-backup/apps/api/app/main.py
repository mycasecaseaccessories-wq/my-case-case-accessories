from __future__ import annotations

import time
import uuid
from contextlib import asynccontextmanager
from typing import Any

from fastapi import APIRouter, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from . import (
    cart_models,  # noqa: F401
    customer_models,  # noqa: F401
    telegram_models,  # noqa: F401
)
from .auth import router as auth_router
from .catalog import router as catalog_router
from .catalog_models import Base
from .config import settings
from .customer import router as customer_router
from .customer_channel import router as customer_channel_router
from .database import engine
from .inventory import router as inventory_router
from .logging_config import configure_logging, logger
from .orders import router as orders_router

configure_logging()


def error_payload(request_id: str, code: str, message: str, details: Any = None) -> dict[str, Any]:
    error: dict[str, Any] = {"code": code, "message": message}
    if details is not None:
        error["details"] = details
    return {"error": error, "request_id": request_id}


@asynccontextmanager
async def lifespan(_: FastAPI):
    logger.info("service_starting", extra={"service": settings.app_name, "environment": settings.app_env})
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()
    logger.info("service_stopped", extra={"service": settings.app_name})


app = FastAPI(title="My Case v1 API", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
api = APIRouter(prefix=settings.api_v1_prefix)


@app.middleware("http")
async def request_context(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    request.state.request_id = request_id
    started = time.perf_counter()
    response = await call_next(request)
    duration_ms = round((time.perf_counter() - started) * 1000, 2)
    response.headers["X-Request-ID"] = request_id
    logger.info(
        "http_request",
        extra={
            "service": settings.app_name,
            "environment": settings.app_env,
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "status": response.status_code,
            "duration_ms": duration_ms,
        },
    )
    return response


@app.exception_handler(RequestValidationError)
async def validation_error(request: Request, exc: RequestValidationError):
    request_id = getattr(request.state, "request_id", "unknown")
    return JSONResponse(
        status_code=422,
        content=error_payload(request_id, "VALIDATION_ERROR", "Request validation failed", exc.errors()),
    )


@app.exception_handler(Exception)
async def unexpected_error(request: Request, _: Exception):
    request_id = getattr(request.state, "request_id", "unknown")
    logger.exception("unhandled_error", extra={"request_id": request_id, "service": settings.app_name})
    return JSONResponse(
        status_code=500, content=error_payload(request_id, "INTERNAL_ERROR", "An unexpected error occurred")
    )


@app.get("/health", tags=["foundation"])
async def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.app_name}


@app.get("/ready", tags=["foundation"])
async def ready() -> Any:
    try:
        async with engine.begin() as connection:
            await connection.execute(text("SELECT 1"))
    except SQLAlchemyError:
        return JSONResponse(status_code=503, content={"status": "not_ready", "dependency": "postgresql"})
    return {"status": "ready", "dependency": "postgresql"}


@api.get("/foundation", tags=["foundation"])
async def foundation() -> dict[str, str]:
    return {"status": "ok", "message": "My Case v1 API foundation"}


app.include_router(api)
app.include_router(catalog_router, prefix=settings.api_v1_prefix)
app.include_router(inventory_router, prefix=settings.api_v1_prefix)
app.include_router(orders_router, prefix=settings.api_v1_prefix)
app.include_router(auth_router, prefix=settings.api_v1_prefix)
app.include_router(customer_router, prefix=settings.api_v1_prefix)
app.include_router(customer_channel_router, prefix=settings.api_v1_prefix)
