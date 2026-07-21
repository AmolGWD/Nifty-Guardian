"""
Persisted Kite Connect session.

Only one row is ever considered "current" - the most recently created
one. The access token itself is stored encrypted (see app.core.security)
and is never exposed outside KiteSessionRepository/KiteAuthService.
"""

from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class KiteSession(Base):
    __tablename__ = "kite_sessions"

    id: Mapped[int] = mapped_column(primary_key=True)

    user_id: Mapped[str]
    user_name: Mapped[str]

    encrypted_access_token: Mapped[str]

    login_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
