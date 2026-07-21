"""
Volatility context, from ATR as a percentage of price (so the
threshold is meaningful regardless of the underlying's absolute level).
"""

from app.trading.context.models import VolatilityContext
from app.trading.indicators.models import IndicatorSnapshot

_HIGH_VOLATILITY_ATR_PERCENT = 0.5


def classify_volatility(snapshot: IndicatorSnapshot) -> VolatilityContext:
    if snapshot.atr_percent >= _HIGH_VOLATILITY_ATR_PERCENT:
        return VolatilityContext.HIGH_VOLATILITY

    return VolatilityContext.LOW_VOLATILITY
