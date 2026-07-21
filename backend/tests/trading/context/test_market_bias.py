from app.trading.context.market_bias import classify_market_bias
from app.trading.context.models import Bias
from app.trading.indicators.trend_direction import TrendDirection
from tests.trading.context.helpers import make_snapshot


def test_bullish_bias_requires_uptrend_and_rsi_above_50() -> None:
    snapshot = make_snapshot(trend_direction=TrendDirection.UPTREND, rsi=60.0)
    assert classify_market_bias(snapshot) == Bias.BULLISH_BIAS


def test_bearish_bias_requires_downtrend_and_rsi_below_50() -> None:
    snapshot = make_snapshot(trend_direction=TrendDirection.DOWNTREND, rsi=40.0)
    assert classify_market_bias(snapshot) == Bias.BEARISH_BIAS


def test_disagreement_is_neutral() -> None:
    snapshot = make_snapshot(trend_direction=TrendDirection.UPTREND, rsi=40.0)
    assert classify_market_bias(snapshot) == Bias.NEUTRAL_BIAS


def test_sideways_trend_is_always_neutral() -> None:
    snapshot = make_snapshot(trend_direction=TrendDirection.SIDEWAYS, rsi=90.0)
    assert classify_market_bias(snapshot) == Bias.NEUTRAL_BIAS
