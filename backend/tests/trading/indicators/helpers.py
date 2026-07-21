from datetime import datetime, timedelta

from app.market_data.schemas import Candle

_BASE_TIME = datetime(2026, 7, 1, 9, 15)


def make_candles(rows: list[tuple[float, float, float, float, int]]) -> list[Candle]:
    """
    rows: list of (open, high, low, close, volume) tuples, oldest first.
    Timestamps are synthetic and evenly spaced - only order matters.
    """
    return [
        Candle(
            timestamp=_BASE_TIME + timedelta(minutes=15 * i),
            open=row[0],
            high=row[1],
            low=row[2],
            close=row[3],
            volume=row[4],
        )
        for i, row in enumerate(rows)
    ]
