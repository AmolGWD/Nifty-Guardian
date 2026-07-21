"""
Open Interest analysis - the standard four-quadrant interpretation of
price change combined with OI change.

Takes plain deltas rather than a market_data schema, for the same
reason as put_call_ratio: Phase 4 doesn't source open interest yet.
"""

from enum import StrEnum


class OpenInterestSignal(StrEnum):
    LONG_BUILDUP = "LONG_BUILDUP"
    SHORT_COVERING = "SHORT_COVERING"
    SHORT_BUILDUP = "SHORT_BUILDUP"
    LONG_UNWINDING = "LONG_UNWINDING"
    NEUTRAL = "NEUTRAL"


def analyze_open_interest(price_change: float, oi_change: float) -> OpenInterestSignal:
    if price_change > 0 and oi_change > 0:
        return OpenInterestSignal.LONG_BUILDUP
    if price_change > 0 and oi_change < 0:
        return OpenInterestSignal.SHORT_COVERING
    if price_change < 0 and oi_change > 0:
        return OpenInterestSignal.SHORT_BUILDUP
    if price_change < 0 and oi_change < 0:
        return OpenInterestSignal.LONG_UNWINDING

    return OpenInterestSignal.NEUTRAL
