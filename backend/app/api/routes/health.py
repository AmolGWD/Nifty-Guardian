"""
Health check endpoint.
"""

import logging

from fastapi import APIRouter

from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health", tags=["Health"])
def health_check() -> dict[str, str]:
    logger.debug("Health check requested")
    return {
        "status": "ok",
        "service": settings.app_name,
        "environment": settings.environment,
    }
