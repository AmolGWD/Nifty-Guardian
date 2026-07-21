"""
Trend context: requires trend_direction and SuperTrend to agree before
calling it a confirmed trend; any disagreement (or trend_direction
itself being sideways) is treated as no clear trend.
"""

from app.trading.context.models import TrendContext
from app.trading.indicators.models import IndicatorSnapshot
from app.trading.indicators.trend_direction import TrendDirection


def classify_trend(snapshot: IndicatorSnapshot) -> TrendContext:
    if snapshot.trend_direction == TrendDirection.UPTREND and snapshot.supertrend_is_bullish:
        return TrendContext.BULLISH_TREND

    if snapshot.trend_direction == TrendDirection.DOWNTREND and not snapshot.supertrend_is_bullish:
        return TrendContext.BEARISH_TREND

    return TrendContext.SIDEWAYS_TREND
