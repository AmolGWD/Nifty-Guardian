"""
Instrument lookup, backed by an in-memory cache of the exchange's
instrument dump, refreshed once per calendar day per exchange.

Stateless with respect to authentication: callers pass in whichever
MarketDataClient is valid for the current request, so this service's
cache can be a long-lived singleton independent of any one client's
lifetime.
"""

import logging
from datetime import date, datetime
from typing import Any

from app.market_data.client import MarketDataClient
from app.market_data.schemas import Instrument

logger = logging.getLogger(__name__)


def _parse_expiry(raw_expiry: object) -> date | None:
    if isinstance(raw_expiry, date):
        return raw_expiry
    if isinstance(raw_expiry, str) and raw_expiry.strip():
        return date.fromisoformat(raw_expiry)
    return None


def _parse_instrument(raw: dict[str, Any]) -> Instrument:
    return Instrument(
        instrument_token=int(raw["instrument_token"]),
        trading_symbol=str(raw["tradingsymbol"]),
        name=str(raw["name"]),
        expiry=_parse_expiry(raw.get("expiry")),
        strike=float(raw["strike"]),
        instrument_type=str(raw["instrument_type"]),
        lot_size=int(raw["lot_size"]),
    )


class InstrumentLookupService:
    def __init__(self) -> None:
        self._cache: dict[str, list[Instrument]] = {}
        self._cached_on: dict[str, date] = {}

    def get_instruments(self, client: MarketDataClient, exchange: str) -> list[Instrument]:
        today = datetime.now().date()

        if self._cached_on.get(exchange) != today:
            logger.info("Refreshing instrument cache for exchange=%s", exchange)
            raw_instruments = client.get_instruments(exchange)
            self._cache[exchange] = [_parse_instrument(row) for row in raw_instruments]
            self._cached_on[exchange] = today

        return self._cache[exchange]

    def find_option(
        self,
        client: MarketDataClient,
        *,
        underlying: str,
        strike: float,
        option_type: str,
        expiry: date,
        exchange: str = "NFO",
    ) -> Instrument | None:
        for instrument in self.get_instruments(client, exchange):
            if (
                instrument.name == underlying
                and instrument.instrument_type == option_type
                and instrument.expiry == expiry
                and instrument.strike == strike
            ):
                return instrument
        return None

    def get_expiries(
        self, client: MarketDataClient, underlying: str, exchange: str = "NFO"
    ) -> list[date]:
        expiries = {
            instrument.expiry
            for instrument in self.get_instruments(client, exchange)
            if instrument.name == underlying
            and instrument.instrument_type in ("CE", "PE")
            and instrument.expiry is not None
        }
        return sorted(expiries)


instrument_lookup_service = InstrumentLookupService()
