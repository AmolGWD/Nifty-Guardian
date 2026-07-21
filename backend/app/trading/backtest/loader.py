"""
Loads historical OHLCV data from CSV into `app.market_data.schemas.Candle`
- the same model the rest of the trading domain already uses. No
separate historical-data type: a candle from a CSV file and a candle
from the live Kite feed are indistinguishable to every downstream
package.

Expected columns (case-insensitive): Timestamp, Open, High, Low,
Close, Volume. Timestamp must be ISO 8601 (e.g. "2026-07-21T09:15:00").
"""

import csv
from datetime import datetime
from pathlib import Path

from app.market_data.schemas import Candle


def load_candles_from_csv(path: str | Path) -> list[Candle]:
    candles: list[Candle] = []

    with open(path, newline="", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            normalized = {key.strip().lower(): value for key, value in row.items()}
            candles.append(
                Candle(
                    timestamp=datetime.fromisoformat(normalized["timestamp"]),
                    open=float(normalized["open"]),
                    high=float(normalized["high"]),
                    low=float(normalized["low"]),
                    close=float(normalized["close"]),
                    volume=int(normalized["volume"]),
                )
            )

    return candles
