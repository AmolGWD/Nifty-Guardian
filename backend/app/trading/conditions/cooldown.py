"""
Cooldown framework: blocks new entries for a configured period after
the last trade closed. No real "last trade closed at" timestamp source
exists yet - paper trading (a later phase) isn't built - so this passes
automatically when none is supplied.
"""

from datetime import datetime

from app.trading.conditions._time_utils import as_ist


def is_cooldown_complete(
    current_timestamp: datetime,
    last_trade_closed_at: datetime | None,
    cooldown_minutes: int,
) -> bool:
    if last_trade_closed_at is None:
        return True

    elapsed_minutes = (
        as_ist(current_timestamp) - as_ist(last_trade_closed_at)
    ).total_seconds() / 60

    return elapsed_minutes >= cooldown_minutes
