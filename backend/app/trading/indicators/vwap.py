"""
Volume Weighted Average Price, over whichever candles are given -
callers decide the window (e.g. today's candles only).
"""

from app.market_data.schemas import Candle


def calculate_vwap(candles: list[Candle]) -> float:
    if not candles:
        raise ValueError("Need at least 1 candle to calculate VWAP")

    cumulative_price_volume = 0.0
    cumulative_volume = 0

    for candle in candles:
        typical_price = (candle.high + candle.low + candle.close) / 3
        cumulative_price_volume += typical_price * candle.volume
        cumulative_volume += candle.volume

    if cumulative_volume == 0:
        raise ValueError("Cannot calculate VWAP with zero total volume")

    return round(cumulative_price_volume / cumulative_volume, 4)
