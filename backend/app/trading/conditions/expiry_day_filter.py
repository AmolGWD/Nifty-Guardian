"""
Expiry day filter: whether trading is permitted on the option's own
expiry day, per configuration (some strategies deliberately avoid the
extreme gamma risk of expiry-day trading).
"""

from datetime import date, datetime

from app.trading.conditions._time_utils import as_ist


def is_expiry_allowed(
    current_timestamp: datetime, expiry_date: date | None, allow_expiry_day_trading: bool
) -> bool:
    if expiry_date is None:
        return True

    is_expiry_day = as_ist(current_timestamp).date() == expiry_date

    return allow_expiry_day_trading or not is_expiry_day
