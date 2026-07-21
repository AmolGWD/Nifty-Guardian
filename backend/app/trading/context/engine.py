"""
Composes the independent context classifiers into one MarketContext.

Input is the IndicatorSnapshot (Phase 5) plus the current market
session state (Phase 4) - session state is fundamentally about wall-
clock time, not a calculated indicator, so it isn't part of
IndicatorSnapshot and is accepted here as a second, explicit input
rather than fabricated from indicator values that have nothing to do
with the time of day.
"""

from datetime import datetime

from app.market_data.market_session import MarketSessionStatus
from app.trading.context.market_bias import classify_market_bias
from app.trading.context.models import MarketContext
from app.trading.context.momentum import classify_momentum
from app.trading.context.option_chain_bias import classify_option_chain_bias
from app.trading.context.overall_state import classify_overall_state
from app.trading.context.trend import classify_trend
from app.trading.context.volatility import classify_volatility
from app.trading.context.volume_strength import classify_volume_strength
from app.trading.indicators.models import IndicatorSnapshot


def build_market_context(
    snapshot: IndicatorSnapshot, session_state: MarketSessionStatus
) -> MarketContext:
    trend = classify_trend(snapshot)
    market_bias = classify_market_bias(snapshot)
    volatility = classify_volatility(snapshot)

    return MarketContext(
        as_of=datetime.now(),
        trend=trend,
        momentum=classify_momentum(snapshot),
        volatility=volatility,
        volume_strength=classify_volume_strength(snapshot),
        market_bias=market_bias,
        option_chain_bias=classify_option_chain_bias(snapshot),
        session_state=session_state,
        overall_state=classify_overall_state(trend, market_bias, volatility),
    )
