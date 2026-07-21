"""
Market session status, based on NSE's regular trading hours.

Does not account for exchange holidays - there is no holiday calendar
data source wired up. This only distinguishes pre-market / open /
closed relative to the configured daily window, purely from the clock.
"""

from datetime import datetime
from enum import StrEnum
from zoneinfo import ZoneInfo

from app.core.config import settings

IST = ZoneInfo("Asia/Kolkata")


class MarketSessionStatus(StrEnum):
    PRE_MARKET = "PRE_MARKET"
    OPEN = "OPEN"
    CLOSED = "CLOSED"


class MarketSessionService:
    def get_status(self, now: datetime | None = None) -> MarketSessionStatus:
        current = (now or datetime.now(IST)).astimezone(IST)
        current_time = current.strftime("%H:%M")

        if current_time < settings.market_open:
            return MarketSessionStatus.PRE_MARKET

        if current_time <= settings.market_close:
            return MarketSessionStatus.OPEN

        return MarketSessionStatus.CLOSED

    def is_open(self, now: datetime | None = None) -> bool:
        return self.get_status(now) == MarketSessionStatus.OPEN


market_session_service = MarketSessionService()
