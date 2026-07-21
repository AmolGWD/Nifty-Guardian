"""
Health check endpoint.
"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter()

DbSession = Annotated[Session, Depends(get_db)]


@router.get("/health", tags=["Health"])
def health_check(db: DbSession) -> dict[str, str]:
    logger.debug("Health check requested")

    try:
        db.execute(text("SELECT 1"))
        database_status = "ok"
    except Exception:
        logger.exception("Database health check failed")
        database_status = "unreachable"

    return {
        "status": "ok",
        "service": settings.app_name,
        "environment": settings.environment,
        "database": database_status,
    }
