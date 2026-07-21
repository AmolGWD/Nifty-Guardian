"""
Kite Connect authentication routes: login redirect and callback.

The redirect URL that Kite sends the browser back to after login must
be registered in the Zerodha developer console for this API key - it
is not passed per-request.
"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.kite.client import build_kite_client
from app.kite.repository import KiteSessionRepository
from app.kite.service import KiteAuthService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth/kite", tags=["Kite Authentication"])


def get_kite_auth_service(db: Annotated[Session, Depends(get_db)]) -> KiteAuthService:
    try:
        client = build_kite_client()
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    return KiteAuthService(client, KiteSessionRepository(db))


KiteAuth = Annotated[KiteAuthService, Depends(get_kite_auth_service)]


@router.get("/login")
def kite_login(auth: KiteAuth) -> RedirectResponse:
    return RedirectResponse(auth.login_url())


@router.get("/callback")
def kite_callback(request_token: str, auth: KiteAuth) -> dict[str, str]:
    try:
        result = auth.complete_login(request_token)
    except RuntimeError as exc:
        # Misconfiguration (e.g. missing KITE_API_SECRET) - not the caller's fault.
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        # Most likely an invalid or expired request_token rejected by Kite.
        logger.exception("Kite login callback failed")
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {
        "status": "success",
        "message": "Kite session established",
        "user_id": result["user_id"],
        "user_name": result["user_name"],
    }
