from app.trading.context.models import TrendContext
from app.trading.context.trend import classify_trend
from app.trading.indicators.trend_direction import TrendDirection
from tests.trading.context.helpers import make_snapshot


def test_bullish_trend_requires_agreement() -> None:
    snapshot = make_snapshot(trend_direction=TrendDirection.UPTREND, supertrend_is_bullish=True)
    assert classify_trend(snapshot) == TrendContext.BULLISH_TREND


def test_bearish_trend_requires_agreement() -> None:
    snapshot = make_snapshot(trend_direction=TrendDirection.DOWNTREND, supertrend_is_bullish=False)
    assert classify_trend(snapshot) == TrendContext.BEARISH_TREND


def test_disagreement_is_sideways() -> None:
    snapshot = make_snapshot(trend_direction=TrendDirection.UPTREND, supertrend_is_bullish=False)
    assert classify_trend(snapshot) == TrendContext.SIDEWAYS_TREND


def test_sideways_trend_direction_is_always_sideways_context() -> None:
    snapshot = make_snapshot(trend_direction=TrendDirection.SIDEWAYS, supertrend_is_bullish=True)
    assert classify_trend(snapshot) == TrendContext.SIDEWAYS_TREND
