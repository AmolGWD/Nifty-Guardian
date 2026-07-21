"""
Zerodha Kite Connect authentication service.

Wraps the login/session-exchange flow behind a Protocol so it can be
tested without the real KiteConnect SDK or a real Zerodha account, and
persists the resulting session via KiteSessionRepository.
"""

import logging
from datetime import datetime
from typing import Any, Protocol

from app.core.config import settings
from app.kite.repository import KiteSessionRepository

logger = logging.getLogger(__name__)


class KiteClientProtocol(Protocol):
    def login_url(self) -> str: ...

    def generate_session(self, request_token: str, api_secret: str) -> dict[str, Any]: ...


class KiteAuthService:
    def __init__(self, client: KiteClientProtocol, repository: KiteSessionRepository) -> None:
        self._client = client
        self._repository = repository

    def login_url(self) -> str:
        return self._client.login_url()

    def complete_login(self, request_token: str) -> dict[str, str]:
        if not settings.kite_api_secret:
            raise RuntimeError("KITE_API_SECRET is not configured")

        session = self._client.generate_session(
            request_token, api_secret=settings.kite_api_secret
        )

        login_time = session["login_time"]
        if isinstance(login_time, str):
            login_time = datetime.fromisoformat(login_time)

        self._repository.save_session(
            user_id=session["user_id"],
            user_name=session["user_name"],
            access_token=session["access_token"],
            login_time=login_time,
        )

        logger.info("Kite session established for user_id=%s", session["user_id"])

        return {"user_id": session["user_id"], "user_name": session["user_name"]}
