"""
NIFTY Guardian v2 - FastAPI application entrypoint.
"""

import logging
import time
import uuid
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.dashboard.dashboard_router import router as dashboard_router
from app.api.dashboard.runtime_router import router as runtime_router
from app.api.routes.deployment import router as deployment_router
from app.api.routes.health import router as health_router
from app.api.routes.kite_auth import router as kite_auth_router
from app.api.routes.market_data import router as market_data_router
from app.api.signals.signals_router import router as signals_router
from app.core.config import settings
from app.core.database import Base, engine

# Importing domain models registers their tables on Base.metadata so
# create_all() below can create them. main.py is the composition root -
# it's the one place allowed to know about every domain model in the app.
from app.kite.models import KiteSession  # noqa: F401
from app.observability.logging import configure_structured_logging, set_request_id
from app.observability.metrics import record_request
from app.observability.startup import run_startup_diagnostics

configure_structured_logging(level=settings.log_level, log_format=settings.log_format)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    logger.info(
        "%s starting up (environment=%s)",
        settings.app_name,
        settings.environment,
    )
    run_startup_diagnostics(settings)
    # create_all only creates missing tables - it does not migrate
    # existing ones. Fine for now; a real schema migration tool
    # (Alembic) should replace this before this app is deployed
    # anywhere with data worth preserving across schema changes.
    Base.metadata.create_all(bind=engine)
    yield
    logger.info("%s shutting down", settings.app_name)


app = FastAPI(
    title=settings.app_name,
    version="2.0.0",
    lifespan=lifespan,
)


# Registered *before* CORSMiddleware below, deliberately. Starlette's
# middleware stack, outer to inner, is:
#   ServerErrorMiddleware -> [add_middleware() calls, most-recent first]
#   -> ExceptionMiddleware -> Router
# CORSMiddleware injects `Access-Control-Allow-Origin` by wrapping the
# ASGI `send` callable as a response streams *out* through it. An
# exception that isn't caught anywhere below CORSMiddleware propagates
# straight past it to ServerErrorMiddleware, which builds the 500 itself
# and sends it directly - CORSMiddleware's `send` wrapper never runs, so
# that response has no CORS headers at all, and the browser reports
# "blocked by CORS policy" instead of showing the real 500.
#
# (`@app.exception_handler(Exception)` does NOT fix this: Starlette
# special-cases a handler registered for `Exception`/500 by installing
# it as ServerErrorMiddleware's own `handler` - i.e. it still runs
# *outside* CORSMiddleware, and still produces a headerless response.
# Verified directly: registering it changed the response body but not
# its headers.)
#
# A plain try/except middleware registered here, before
# `app.add_middleware(CORSMiddleware, ...)`, ends up *inside* CORSMiddleware
# (earlier add_middleware() calls end up closer to the router). It
# catches the exception before it can escape past CORSMiddleware,
# returning a normal Response that flows back out through CORSMiddleware
# (and gets Access-Control-Allow-Origin) exactly like any other response.
@app.middleware("http")
async def catch_unhandled_exceptions_middleware(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    try:
        return await call_next(request)
    except Exception:
        logger.exception("Unhandled exception for %s %s", request.method, request.url.path)
        return JSONResponse(status_code=500, content={"detail": "Internal server error"})


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_id_and_metrics_middleware(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    """
    Assigns a request ID (reused from `X-Request-ID` if the caller
    already supplied one, e.g. a load balancer), attaches it to every
    log record emitted while handling this request, and records a
    basic request-count/latency metric. No trading logic touches this
    - it wraps every route uniformly.
    """
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    set_request_id(request_id)
    start = time.monotonic()
    try:
        response = await call_next(request)
    finally:
        set_request_id(None)
    duration = time.monotonic() - start
    response.headers["X-Request-ID"] = request_id
    record_request(
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        duration_seconds=duration,
    )
    return response


app.include_router(health_router)
app.include_router(deployment_router)
app.include_router(kite_auth_router)
app.include_router(market_data_router)
app.include_router(dashboard_router)
app.include_router(runtime_router)
app.include_router(signals_router)
