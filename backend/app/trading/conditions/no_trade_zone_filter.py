"""
No-Trade Zone: blocks new entries either in the final N minutes before
market close (end-of-day volatility/gap risk into the next session),
or whenever the Market Context Engine classifies the overall market as
VolatileRange (choppy, high-volatility sideways action). Both are
permission gates based on when/what-state it is - neither is a
directional trading decision.
"""

from datetime import datetime

from app.trading.conditions._time_utils import (
    current_minutes_since_midnight,
    minutes_since_midnight,
)
from app.trading.context.models import MarketContext, OverallMarketState


def is_within_no_trade_zone(
    current_timestamp: datetime,
    market_close: str,
    no_trade_zone_minutes: int,
    market_context: MarketContext,
) -> bool:
    zone_start = minutes_since_midnight(market_close) - no_trade_zone_minutes
    is_end_of_day_zone = current_minutes_since_midnight(current_timestamp) >= zone_start
    is_volatile_range = market_context.overall_state == OverallMarketState.VOLATILE_RANGE

    return is_end_of_day_zone or is_volatile_range
