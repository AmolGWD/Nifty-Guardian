"""
Overall Market State: synthesizes the already-classified Trend, Market
Bias, and Volatility into one summary label.

Unlike the other classifiers in this package, this one takes already-
computed context values rather than the raw IndicatorSnapshot - it is
the one legitimate composition point, mirroring how
app.trading.indicators.engine composes indicator calculators.
"""

from app.trading.context.models import Bias, OverallMarketState, TrendContext, VolatilityContext


def classify_overall_state(
    trend: TrendContext, market_bias: Bias, volatility: VolatilityContext
) -> OverallMarketState:
    if trend == TrendContext.SIDEWAYS_TREND:
        if volatility == VolatilityContext.HIGH_VOLATILITY:
            return OverallMarketState.VOLATILE_RANGE
        return OverallMarketState.RANGE_BOUND

    if trend == TrendContext.BULLISH_TREND and market_bias == Bias.BULLISH_BIAS:
        return OverallMarketState.STRONG_BULLISH

    if trend == TrendContext.BEARISH_TREND and market_bias == Bias.BEARISH_BIAS:
        return OverallMarketState.STRONG_BEARISH

    return OverallMarketState.MIXED
