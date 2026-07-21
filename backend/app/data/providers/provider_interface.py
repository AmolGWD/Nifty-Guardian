"""
Common interface every historical data provider implements - a plain
date-range fetch, so the platform can treat a CSV file and a future
network provider identically. No provider here performs network
access this phase (see `stub_providers.py`).
"""

from datetime import datetime
from typing import Protocol

from app.data.models import OHLCVRecord


class HistoricalDataProvider(Protocol):
    def fetch(self, start: datetime, end: datetime) -> list[OHLCVRecord]: ...
