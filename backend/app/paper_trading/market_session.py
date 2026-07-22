"""
Market session abstraction: Pre-open/Open/Lunch/Close/After-hours/
Holiday phases, deliberately with no NSE-specific calendar baked in
anywhere - `MarketCalendar` is a `Protocol`, and `ConfigurableCalendar`
is a reference implementation whose windows and holiday set are all
constructor parameters, not constants. This is intentionally distinct
from (not a replacement for) `app.market_data.market_session`
(frozen, Phase 4) - that module only distinguishes PRE_MARKET/OPEN/
CLOSED from the clock, has no lunch/holiday concept, and reads its
windows from global `app.core.config.settings`, not per-instance
configuration; this module is Paper Trading's own, richer session
model, built for this package's specific need to model a lunch break
and market holidays.

A caller who wants a real NSE calendar constructs a `ConfigurableCalendar`
with NSE's actual hours and holiday list - that data does not belong in
this framework code.
"""

from datetime import date, datetime, time
from enum import StrEnum
from typing import Protocol

from pydantic import BaseModel, ConfigDict, model_validator

from app.config.validation import ParameterValidationError


class SessionPhase(StrEnum):
    PRE_OPEN = "PreOpen"
    OPEN = "Open"
    LUNCH = "Lunch"
    CLOSE = "Close"
    AFTER_HOURS = "AfterHours"
    HOLIDAY = "Holiday"


class MarketCalendar(Protocol):
    def is_trading_day(self, day: date) -> bool: ...

    def session_phase(self, timestamp: datetime) -> SessionPhase: ...


class SessionWindows(BaseModel):
    model_config = ConfigDict(frozen=True)

    pre_open_start: time
    open_start: time
    open_end: time
    lunch_start: time | None = None
    lunch_end: time | None = None
    after_hours_end: time | None = None

    @model_validator(mode="after")
    def _validate(self) -> "SessionWindows":
        if not (self.pre_open_start < self.open_start < self.open_end):
            raise ParameterValidationError(
                "pre_open_start must be before open_start, which must be before open_end"
            )
        if (self.lunch_start is None) != (self.lunch_end is None):
            raise ParameterValidationError("lunch_start and lunch_end must be set together")
        if (
            self.lunch_start is not None
            and self.lunch_end is not None
            and not (self.open_start < self.lunch_start < self.lunch_end < self.open_end)
        ):
            raise ParameterValidationError("lunch window must fall strictly within the open window")
        if self.after_hours_end is not None and self.after_hours_end <= self.open_end:
            raise ParameterValidationError("after_hours_end must be after open_end")
        return self


class ConfigurableCalendar:
    """
    A `MarketCalendar` built entirely from constructor arguments - no
    hardcoded exchange, no hardcoded holiday. `holidays` is an
    explicit `set[date]` the caller supplies (e.g., loaded from a
    file, a database, or a real exchange calendar API elsewhere) -
    this class never reasons about which dates are holidays on its
    own.
    """

    def __init__(self, windows: SessionWindows, *, holidays: set[date] | None = None) -> None:
        self._windows = windows
        self._holidays = holidays if holidays is not None else set()

    def is_trading_day(self, day: date) -> bool:
        return day.isoweekday() not in (6, 7) and day not in self._holidays

    def session_phase(self, timestamp: datetime) -> SessionPhase:
        if not self.is_trading_day(timestamp.date()):
            return SessionPhase.HOLIDAY

        current_time = timestamp.time()
        windows = self._windows

        if current_time < windows.pre_open_start:
            # Before today's pre-open is still the previous session's after-hours window,
            # from a clock-time-only read with no concept of which calendar day it belongs to
            # (the same limitation already flagged for app.market_data.market_session).
            return SessionPhase.AFTER_HOURS
        if current_time < windows.open_start:
            return SessionPhase.PRE_OPEN
        if (
            windows.lunch_start is not None
            and windows.lunch_end is not None
            and windows.lunch_start <= current_time < windows.lunch_end
        ):
            return SessionPhase.LUNCH
        if current_time < windows.open_end:
            return SessionPhase.OPEN
        if windows.after_hours_end is not None and current_time < windows.after_hours_end:
            return SessionPhase.AFTER_HOURS
        return SessionPhase.CLOSE
