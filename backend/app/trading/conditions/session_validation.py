"""
Trading session validation: the market must be open AND it must be a
weekday. There is no exchange holiday calendar wired up anywhere in
this codebase (flagged since Phase 4) - this does not account for
market holidays that fall on a weekday.
"""

from datetime import datetime

from app.market_data.market_session import MarketSessionStatus
from app.trading.conditions._time_utils import as_ist

_WEEKEND_ISOWEEKDAYS = (6, 7)  # Saturday, Sunday


def is_session_valid(session_state: MarketSessionStatus, current_timestamp: datetime) -> bool:
    if session_state != MarketSessionStatus.OPEN:
        return False

    return as_ist(current_timestamp).isoweekday() not in _WEEKEND_ISOWEEKDAYS
