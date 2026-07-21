"""
Expiry discovery for a given underlying's option chain.

Nearest expiry is derived from the actual instrument dump (earliest
expiry on or after today), never from an assumed weekday - exchange
expiry-day conventions change over time and shouldn't be hardcoded.
"""

from datetime import date, datetime

from app.market_data.client import MarketDataClient
from app.market_data.instrument_lookup import InstrumentLookupService, instrument_lookup_service


class ExpiryDiscoveryService:
    def __init__(self, instrument_lookup: InstrumentLookupService) -> None:
        self._instrument_lookup = instrument_lookup

    def get_available_expiries(
        self, client: MarketDataClient, underlying: str, exchange: str = "NFO"
    ) -> list[date]:
        return self._instrument_lookup.get_expiries(client, underlying, exchange)

    def get_nearest_expiry(
        self, client: MarketDataClient, underlying: str, exchange: str = "NFO"
    ) -> date | None:
        today = datetime.now().date()
        upcoming = [
            expiry
            for expiry in self.get_available_expiries(client, underlying, exchange)
            if expiry >= today
        ]
        return upcoming[0] if upcoming else None


expiry_discovery_service = ExpiryDiscoveryService(instrument_lookup_service)
