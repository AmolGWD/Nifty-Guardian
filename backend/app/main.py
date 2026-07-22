"""
NIFTY Guardian v2 - FastAPI application entrypoint.
"""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.dashboard.dashboard_router import router as dashboard_router
from app.api.dashboard.runtime_router import router as runtime_router
from app.api.routes.health import router as health_router
from app.api.routes.kite_auth import router as kite_auth_router
from app.api.routes.market_data import router as market_data_router
from app.core.config import settings
from app.core.database import Base, engine
from app.core.logging import configure_logging

# Importing domain models registers their tables on Base.metadata so
# create_all() below can create them. main.py is the composition root -
# it's the one place allowed to know about every domain model in the app.
from app.kite.models import KiteSession  # noqa: F401

configure_logging()

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    logger.info(
        "%s starting up (environment=%s)",
        settings.app_name,
        settings.environment,
    )
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

app.include_router(health_router)
app.include_router(kite_auth_router)
app.include_router(market_data_router)
app.include_router(dashboard_router)
app.include_router(runtime_router)
