"""
CSV-backed HistoricalDataProvider. Deliberately independent of
`app.trading.backtest.loader` (Phase 11, frozen) rather than reusing
it - the dependency direction for this platform must run the other
way (backtesting will eventually consume `app.data`, not the reverse),
so `app.data` cannot depend on `app.trading.backtest` without
inverting that. It parses into `OHLCVRecord`, this platform's own
storage model (see `app.data.models` for why that's a distinct type
from `app.market_data.schemas.Candle`), not into the Candle Phase 11
uses.
"""

import csv
from datetime import datetime
from pathlib import Path

from app.data.models import OHLCVRecord


class CSVHistoricalDataProvider:
    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)

    def fetch(self, start: datetime, end: datetime) -> list[OHLCVRecord]:
        return [record for record in self._load_all() if start <= record.timestamp <= end]

    def _load_all(self) -> list[OHLCVRecord]:
        records: list[OHLCVRecord] = []

        with open(self._path, newline="", encoding="utf-8") as csv_file:
            reader = csv.DictReader(csv_file)
            for row in reader:
                normalized = {key.strip().lower(): value for key, value in row.items()}
                open_interest_raw = normalized.get("open_interest")

                records.append(
                    OHLCVRecord(
                        timestamp=datetime.fromisoformat(normalized["timestamp"]),
                        open=float(normalized["open"]),
                        high=float(normalized["high"]),
                        low=float(normalized["low"]),
                        close=float(normalized["close"]),
                        volume=int(normalized["volume"]),
                        open_interest=int(open_interest_raw) if open_interest_raw else None,
                    )
                )

        return records
