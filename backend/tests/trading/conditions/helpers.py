from datetime import datetime

from app.market_data.market_session import MarketSessionStatus
from app.trading.context.models import (
    Bias,
    MarketContext,
    MomentumContext,
    OverallMarketState,
    TrendContext,
    VolatilityContext,
    VolumeStrengthContext,
)


def make_market_context(
    *,
    overall_state: OverallMarketState = OverallMarketState.RANGE_BOUND,
    session_state: MarketSessionStatus = MarketSessionStatus.OPEN,
) -> MarketContext:
    return MarketContext(
        as_of=datetime(2026, 7, 21, 10, 0),
        trend=TrendContext.SIDEWAYS_TREND,
        momentum=MomentumContext.WEAK_MOMENTUM,
        volatility=VolatilityContext.LOW_VOLATILITY,
        volume_strength=VolumeStrengthContext.AVERAGE_VOLUME,
        market_bias=Bias.NEUTRAL_BIAS,
        option_chain_bias=Bias.NEUTRAL_BIAS,
        session_state=session_state,
        overall_state=overall_state,
    )
