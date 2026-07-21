"""
Market Bias: requires trend direction and RSI direction (above/below
50) to agree before calling a directional bias - otherwise neutral.

Distinct from Trend (which only checks trend_direction vs SuperTrend):
this checks trend_direction vs RSI, giving an independent second
opinion on directional tilt rather than repeating the same check.
"""

from app.trading.context.models import Bias
from app.trading.indicators.models import IndicatorSnapshot
from app.trading.indicators.trend_direction import TrendDirection


def classify_market_bias(snapshot: IndicatorSnapshot) -> Bias:
    if snapshot.trend_direction == TrendDirection.UPTREND and snapshot.rsi > 50:
        return Bias.BULLISH_BIAS

    if snapshot.trend_direction == TrendDirection.DOWNTREND and snapshot.rsi < 50:
        return Bias.BEARISH_BIAS

    return Bias.NEUTRAL_BIAS
