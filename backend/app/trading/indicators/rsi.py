"""
Relative Strength Index (Wilder's smoothing method).
"""

from app.market_data.schemas import Candle


def calculate_rsi(candles: list[Candle], period: int = 14) -> float:
    if len(candles) < period + 1:
        raise ValueError(
            f"Need at least {period + 1} candles to calculate RSI({period}), got {len(candles)}"
        )

    closes = [c.close for c in candles]
    deltas = [closes[i] - closes[i - 1] for i in range(1, len(closes))]

    gains = [max(delta, 0.0) for delta in deltas]
    losses = [max(-delta, 0.0) for delta in deltas]

    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period

    for i in range(period, len(gains)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period

    if avg_loss == 0:
        return 100.0

    relative_strength = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + relative_strength))

    return round(rsi, 4)
