"""
SuperTrend.

Computes its own ATR internally as a private helper - this is not a
dependency on another indicator, since ATR is not one of the 8 output
indicators, just an intermediate step of SuperTrend's own algorithm.
"""

from pydantic import BaseModel, ConfigDict

from app.market_data.schemas import Candle


class SuperTrendResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    value: float
    is_bullish: bool


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


def _average_true_range(candles: list[Candle], period: int) -> list[float]:
    true_ranges = _true_ranges(candles)

    atr = sum(true_ranges[:period]) / period
    atr_values = [atr] * period

    for i in range(period, len(true_ranges)):
        atr = (atr * (period - 1) + true_ranges[i]) / period
        atr_values.append(atr)

    return atr_values


def calculate_supertrend(
    candles: list[Candle], period: int = 10, multiplier: float = 3.0
) -> SuperTrendResult:
    if len(candles) <= period:
        raise ValueError(
            f"Need more than {period} candles to calculate SuperTrend({period}), got {len(candles)}"
        )

    atr_values = _average_true_range(candles, period)

    final_upperband = [0.0] * len(candles)
    final_lowerband = [0.0] * len(candles)
    is_bullish = [True] * len(candles)

    for i in range(period, len(candles)):
        hl2 = (candles[i].high + candles[i].low) / 2
        basic_upper = hl2 + multiplier * atr_values[i]
        basic_lower = hl2 - multiplier * atr_values[i]

        if i == period:
            final_upperband[i] = basic_upper
            final_lowerband[i] = basic_lower
            is_bullish[i] = candles[i].close >= final_lowerband[i]
            continue

        prev_close = candles[i - 1].close

        final_upperband[i] = (
            basic_upper
            if basic_upper < final_upperband[i - 1] or prev_close > final_upperband[i - 1]
            else final_upperband[i - 1]
        )
        final_lowerband[i] = (
            basic_lower
            if basic_lower > final_lowerband[i - 1] or prev_close < final_lowerband[i - 1]
            else final_lowerband[i - 1]
        )

        if is_bullish[i - 1]:
            is_bullish[i] = candles[i].close >= final_lowerband[i]
        else:
            is_bullish[i] = candles[i].close > final_upperband[i]

    latest_is_bullish = is_bullish[-1]
    latest_value = final_lowerband[-1] if latest_is_bullish else final_upperband[-1]

    return SuperTrendResult(value=round(latest_value, 4), is_bullish=latest_is_bullish)
