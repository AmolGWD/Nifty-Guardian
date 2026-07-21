"""
Single adapter boundary between the Market Data module and the Kite
Connect SDK.

Every Kite SDK call used anywhere in app.market_data goes through this
Protocol. Nothing else in this package imports kiteconnect directly,
and every service in this package is written against MarketDataClient,
never against KiteConnect - that's what makes the whole module
testable with a fake and swappable to a different data provider later.
"""

from datetime import datetime
from typing import Any, Protocol

from kiteconnect import KiteConnect


class MarketDataClient(Protocol):
    def get_ltp(self, instruments: list[str]) -> dict[str, dict[str, Any]]: ...

    def get_historical_data(
        self,
        instrument_token: int,
        from_date: datetime,
        to_date: datetime,
        interval: str,
    ) -> list[dict[str, Any]]: ...

    def get_instruments(self, exchange: str) -> list[dict[str, Any]]: ...


class KiteMarketDataClient:
    """Adapts an already-authenticated KiteConnect instance to MarketDataClient."""

    def __init__(self, kite: KiteConnect) -> None:
        self._kite = kite

    def get_ltp(self, instruments: list[str]) -> dict[str, dict[str, Any]]:
        return dict(self._kite.ltp(instruments))

    def get_historical_data(
        self,
        instrument_token: int,
        from_date: datetime,
        to_date: datetime,
        interval: str,
    ) -> list[dict[str, Any]]:
        return list(
            self._kite.historical_data(
                instrument_token=instrument_token,
                from_date=from_date,
                to_date=to_date,
                interval=interval,
            )
        )

    def get_instruments(self, exchange: str) -> list[dict[str, Any]]:
        return list(self._kite.instruments(exchange))
