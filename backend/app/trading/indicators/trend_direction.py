"""
Trend Direction - classic higher-high/higher-low (uptrend) vs
lower-high/lower-low (downtrend) swing comparison, splitting the given
candles into a first and second half.
"""

from enum import StrEnum

from app.market_data.schemas import Candle


class TrendDirection(StrEnum):
    UPTREND = "UPTREND"
    DOWNTREND = "DOWNTREND"
    SIDEWAYS = "SIDEWAYS"


def determine_trend(candles: list[Candle]) -> TrendDirection:
    if len(candles) < 2:
        raise ValueError("Need at least 2 candles to determine trend direction")

    midpoint = len(candles) // 2
    first_half = candles[:midpoint]
    second_half = candles[midpoint:]

    first_high = max(c.high for c in first_half)
    first_low = min(c.low for c in first_half)
    second_high = max(c.high for c in second_half)
    second_low = min(c.low for c in second_half)

    higher_high = second_high > first_high
    higher_low = second_low > first_low
    lower_high = second_high < first_high
    lower_low = second_low < first_low

    if higher_high and higher_low:
        return TrendDirection.UPTREND
    if lower_high and lower_low:
        return TrendDirection.DOWNTREND

    return TrendDirection.SIDEWAYS
