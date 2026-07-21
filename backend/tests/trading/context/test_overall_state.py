from app.trading.context.models import Bias, OverallMarketState, TrendContext, VolatilityContext
from app.trading.context.overall_state import classify_overall_state


def test_strong_bullish() -> None:
    result = classify_overall_state(
        TrendContext.BULLISH_TREND, Bias.BULLISH_BIAS, VolatilityContext.LOW_VOLATILITY
    )
    assert result == OverallMarketState.STRONG_BULLISH


def test_strong_bearish() -> None:
    result = classify_overall_state(
        TrendContext.BEARISH_TREND, Bias.BEARISH_BIAS, VolatilityContext.LOW_VOLATILITY
    )
    assert result == OverallMarketState.STRONG_BEARISH


def test_range_bound_sideways_low_volatility() -> None:
    result = classify_overall_state(
        TrendContext.SIDEWAYS_TREND, Bias.NEUTRAL_BIAS, VolatilityContext.LOW_VOLATILITY
    )
    assert result == OverallMarketState.RANGE_BOUND


def test_volatile_range_sideways_high_volatility() -> None:
    result = classify_overall_state(
        TrendContext.SIDEWAYS_TREND, Bias.NEUTRAL_BIAS, VolatilityContext.HIGH_VOLATILITY
    )
    assert result == OverallMarketState.VOLATILE_RANGE


def test_mixed_when_trend_and_bias_disagree() -> None:
    result = classify_overall_state(
        TrendContext.BULLISH_TREND, Bias.BEARISH_BIAS, VolatilityContext.LOW_VOLATILITY
    )
    assert result == OverallMarketState.MIXED
