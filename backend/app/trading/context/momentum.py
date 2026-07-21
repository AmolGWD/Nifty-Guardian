"""
Momentum context: how far RSI sits from the neutral midpoint (50),
regardless of direction - this is about strength, not direction (that's
Market Bias's job).
"""

from app.trading.context.models import MomentumContext
from app.trading.indicators.models import IndicatorSnapshot

_STRONG_MOMENTUM_RSI_DISTANCE = 20.0


def classify_momentum(snapshot: IndicatorSnapshot) -> MomentumContext:
    distance_from_midpoint = abs(snapshot.rsi - 50.0)

    if distance_from_midpoint >= _STRONG_MOMENTUM_RSI_DISTANCE:
        return MomentumContext.STRONG_MOMENTUM

    return MomentumContext.WEAK_MOMENTUM
