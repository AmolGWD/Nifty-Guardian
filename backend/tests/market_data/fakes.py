"""
A fake MarketDataClient for testing the market data layer without any
real network calls, real credentials, or the real Kite SDK.
"""

from datetime import datetime
from typing import Any


class FakeMarketDataClient:
    def __init__(
        self,
        ltp_responses: dict[str, dict[str, Any]] | None = None,
        historical_data: list[dict[str, Any]] | None = None,
        instruments: list[dict[str, Any]] | None = None,
    ) -> None:
        self._ltp_responses = ltp_responses or {}
        self._historical_data = historical_data or []
        self._instruments = instruments or []
        self.instrument_fetch_count = 0

    def get_ltp(self, instruments: list[str]) -> dict[str, dict[str, Any]]:
        return {symbol: self._ltp_responses[symbol] for symbol in instruments}

    def get_historical_data(
        self,
        instrument_token: int,
        from_date: datetime,
        to_date: datetime,
        interval: str,
    ) -> list[dict[str, Any]]:
        return self._historical_data

    def get_instruments(self, exchange: str) -> list[dict[str, Any]]:
        self.instrument_fetch_count += 1
        return self._instruments
