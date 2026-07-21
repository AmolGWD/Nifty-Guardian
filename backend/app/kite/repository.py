"""
Persistence for Kite Connect sessions.

Access tokens are encrypted before being written and decrypted only
when actually read back out - callers of get_valid_access_token()
receive a plaintext token, but nothing else in this module ever does.
"""

from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.repository import Repository
from app.core.security import decrypt, encrypt
from app.kite.models import KiteSession

IST = ZoneInfo("Asia/Kolkata")


class KiteSessionRepository(Repository[KiteSession]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, KiteSession)

    def save_session(
        self,
        *,
        user_id: str,
        user_name: str,
        access_token: str,
        login_time: datetime,
    ) -> KiteSession:
        return self.add(
            KiteSession(
                user_id=user_id,
                user_name=user_name,
                encrypted_access_token=encrypt(access_token),
                login_time=login_time,
            )
        )

    def get_latest(self) -> KiteSession | None:
        return self._session.scalars(
            select(KiteSession).order_by(KiteSession.id.desc()).limit(1)
        ).first()

    def get_valid_access_token(self) -> str | None:
        """
        Returns the current access token if the most recent login was
        today (Kite access tokens expire daily). This is a same-day
        heuristic, not an exact replica of Kite's expiry algorithm -
        the authoritative check is always the Kite API itself raising
        TokenException on an actually-expired token.
        """
        latest = self.get_latest()

        if latest is None:
            return None

        login_time = latest.login_time
        if login_time.tzinfo is None:
            login_time = login_time.replace(tzinfo=IST)
        else:
            login_time = login_time.astimezone(IST)

        if login_time.date() != datetime.now(IST).date():
            return None

        return decrypt(latest.encrypted_access_token)
