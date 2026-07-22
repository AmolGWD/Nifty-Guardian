from datetime import datetime, timedelta

from app.market_data.schemas import Candle


def build_candles(
    n: int,
    *,
    start: datetime = datetime(2026, 1, 5, 9, 15),
    per_day: int = 25,
    trend: bool = True,
) -> list[Candle]:
    """
    Synthetic weekday-only 15-minute candles in a mild uptrend (enough to
    trigger the EMA breakout strategy after warmup) - mirrors the pattern
    already used by scripts/demo_paper_architecture.py and demo_pipeline.py.
    """
    candles: list[Candle] = []
    timestamp = start
    close = 100.0
    count_today = 0

    while len(candles) < n:
        if timestamp.weekday() >= 5:
            timestamp += timedelta(days=1)
            continue

        open_price = close
        close = close + 2.0 if trend else close + (1.0 if len(candles) % 2 == 0 else -1.0)
        high = max(open_price, close) + 1.0
        low = min(open_price, close) - 1.0
        candles.append(
            Candle(
                timestamp=timestamp, open=open_price, high=high, low=low, close=close,
                volume=10_000,
            )
        )
        timestamp += timedelta(minutes=15)
        count_today += 1
        if count_today >= per_day:
            timestamp += timedelta(hours=16)
            count_today = 0

    return candles
