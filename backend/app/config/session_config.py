"""
SessionParameters - documents the CTO brief's SessionConfig examples
(Opening Range Minutes, Trading Start/End Time, Lunch Filter, Expiry
Filter), but is NOT wired into anything this phase.

Every one of these fields maps onto app.trading.conditions, which is
explicitly frozen this phase - "Modify ONLY the strategy and risk
modules where necessary" (CTO brief) rules out touching it. This model
exists so the parameter is documented and validated (per the brief's
PARAMETER CATALOG / VALIDATION sections) with the honest shape it will
need later, without inventing a fake connection today - the same
"unconnected placeholder" pattern as Phase 14's Experiment.parameters
(see docs/RESEARCH_GUIDE.md, "Parameter management").

Defaults for opening_range_minutes/no_trade_zone_minutes/
allow_expiry_day_trading mirror
app.trading.conditions.engine.build_trading_conditions's own existing
defaults, so this placeholder's implied "current behavior" is accurate.
trading_start_time/trading_end_time mirror app.core.config.Settings'
market_open/market_close. lunch_filter_enabled has no existing
counterpart anywhere in this codebase - there is no midday/lunch-break
concept in app.trading.conditions today (only an end-of-day
"no-trade-zone" and a market-open opening-range filter) - so it defaults
to False and is documented as inert.
"""

from pydantic import BaseModel, ConfigDict, model_validator

from app.config.defaults import (
    DEFAULT_ALLOW_EXPIRY_DAY_TRADING,
    DEFAULT_LUNCH_FILTER_ENABLED,
    DEFAULT_NO_TRADE_ZONE_MINUTES,
    DEFAULT_OPENING_RANGE_MINUTES,
    DEFAULT_TRADING_END_TIME,
    DEFAULT_TRADING_START_TIME,
)
from app.config.validation import ParameterValidationError, validate_range


def _parse_hhmm(name: str, value: str) -> tuple[int, int]:
    try:
        hour_str, minute_str = value.split(":")
        hour, minute = int(hour_str), int(minute_str)
    except ValueError as exc:
        raise ParameterValidationError(f"{name}={value!r} is not a valid HH:MM time") from exc
    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        raise ParameterValidationError(f"{name}={value!r} is not a valid HH:MM time")
    return hour, minute


class SessionParameters(BaseModel):
    model_config = ConfigDict(frozen=True)

    opening_range_minutes: int = DEFAULT_OPENING_RANGE_MINUTES
    no_trade_zone_minutes: int = DEFAULT_NO_TRADE_ZONE_MINUTES
    trading_start_time: str = DEFAULT_TRADING_START_TIME
    trading_end_time: str = DEFAULT_TRADING_END_TIME
    allow_expiry_day_trading: bool = DEFAULT_ALLOW_EXPIRY_DAY_TRADING
    lunch_filter_enabled: bool = DEFAULT_LUNCH_FILTER_ENABLED

    @model_validator(mode="after")
    def _validate(self) -> "SessionParameters":
        validate_range("opening_range_minutes", self.opening_range_minutes, 0, 120)
        validate_range("no_trade_zone_minutes", self.no_trade_zone_minutes, 0, 120)
        start_hour, start_minute = _parse_hhmm("trading_start_time", self.trading_start_time)
        end_hour, end_minute = _parse_hhmm("trading_end_time", self.trading_end_time)
        if (start_hour, start_minute) >= (end_hour, end_minute):
            raise ParameterValidationError(
                f"trading_start_time={self.trading_start_time} must be before "
                f"trading_end_time={self.trading_end_time}"
            )
        return self
