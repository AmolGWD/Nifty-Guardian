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

from app.api.dashboard.dashboard_router import router as dashboard_router
from app.api.dashboard.runtime_router import router as runtime_router
from app.api.routes.deployment import router as deployment_router
from app.api.routes.health import router as health_router
from app.api.routes.kite_auth import router as kite_auth_router
from app.api.routes.market_data import router as market_data_router
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
