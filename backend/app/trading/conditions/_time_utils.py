"""
Shared time-parsing helpers for the condition evaluators.

Not an evaluator itself - just parsing "HH:MM" config strings and
normalizing timestamps to IST, the same pattern already used in
app.kite.repository for Kite session staleness checks.
"""

from datetime import datetime
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")


def minutes_since_midnight(hhmm: str) -> int:
    hour, minute = (int(part) for part in hhmm.split(":"))
    return hour * 60 + minute


def as_ist(timestamp: datetime) -> datetime:
    if timestamp.tzinfo is None:
        return timestamp.replace(tzinfo=IST)
    return timestamp.astimezone(IST)


def current_minutes_since_midnight(timestamp: datetime) -> int:
    ist_time = as_ist(timestamp)
    return ist_time.hour * 60 + ist_time.minute
