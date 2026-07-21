"""
First-N-minute opening range restriction - avoids trading in the
volatile first few minutes right after market open.
"""

from datetime import datetime

from app.trading.conditions._time_utils import (
    current_minutes_since_midnight,
    minutes_since_midnight,
)


def is_opening_range_complete(
    current_timestamp: datetime, market_open: str, opening_range_minutes: int
) -> bool:
    end_of_opening_range = minutes_since_midnight(market_open) + opening_range_minutes
    return current_minutes_since_midnight(current_timestamp) >= end_of_opening_range
