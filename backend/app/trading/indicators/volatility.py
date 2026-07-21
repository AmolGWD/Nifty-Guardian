"""
Average True Range and ATR-as-percentage-of-price - the volatility
measure exposed by the Indicator Engine.

Computes its own true-range series rather than importing SuperTrend's
private ATR helper, to keep every indicator in this package independent
of every other one (per this package's own rule) - a little duplicated
math in exchange for that independence.
"""

from app.market_data.schemas import Candle


def _true_ranges(candles: list[Candle]) -> list[float]:
    ranges = []
    for i, candle in enumerate(candles):
        if i == 0:
            ranges.append(candle.high - candle.low)
        else:
            prev_close = candles[i - 1].close
            ranges.append(
                max(
                    candle.high - candle.low,
                    abs(candle.high - prev_close),
                    abs(candle.low - prev_close),
                )
            )
    return ranges


def calculate_atr(candles: list[Candle], period: int = 14) -> float:
    if len(candles) < period:
        raise ValueError(
            f"Need at least {period} candles to calculate ATR({period}), got {len(candles)}"
        )

    true_ranges = _true_ranges(candles)
    atr = sum(true_ranges[:period]) / period

    for i in range(period, len(true_ranges)):
        atr = (atr * (period - 1) + true_ranges[i]) / period

    return round(atr, 4)


def calculate_atr_percent(candles: list[Candle], period: int = 14) -> float:
    atr = calculate_atr(candles, period=period)
    latest_close = candles[-1].close

    if latest_close == 0:
        raise ValueError("Cannot calculate ATR percent with a zero closing price")

    return round((atr / latest_close) * 100, 4)
