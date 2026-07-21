"""
Exponential Moving Average.
"""

from app.market_data.schemas import Candle


def calculate_ema(candles: list[Candle], period: int = 20) -> float:
    if len(candles) < period:
        raise ValueError(
            f"Need at least {period} candles to calculate EMA({period}), got {len(candles)}"
        )

    closes = [c.close for c in candles]
    multiplier = 2 / (period + 1)

    ema = sum(closes[:period]) / period

    for close in closes[period:]:
        ema = (close - ema) * multiplier + ema

    return round(ema, 4)
