"""
Option chain for a given underlying and expiry: every CE/PE contract
with its current live premium.

Deliberately returns the whole chain rather than picking out "the ATM
one" - deciding which contract to act on is a trading decision, out of
scope for this module.
"""

from datetime import date

from app.market_data.client import MarketDataClient
from app.market_data.instrument_lookup import InstrumentLookupService, instrument_lookup_service
from app.market_data.schemas import OptionContract


class OptionChainService:
    def __init__(self, instrument_lookup: InstrumentLookupService) -> None:
        self._instrument_lookup = instrument_lookup

    def get_option_chain(
        self,
        client: MarketDataClient,
        underlying: str,
        expiry: date,
        exchange: str = "NFO",
    ) -> list[OptionContract]:
        contracts = [
            instrument
            for instrument in self._instrument_lookup.get_instruments(client, exchange)
            if instrument.name == underlying
            and instrument.expiry == expiry
            and instrument.instrument_type in ("CE", "PE")
        ]

        if not contracts:
            return []

        symbols = [f"{exchange}:{contract.trading_symbol}" for contract in contracts]
        quotes = client.get_ltp(symbols)

        return [
            OptionContract(
                instrument=contract,
                last_price=float(
                    quotes[f"{exchange}:{contract.trading_symbol}"]["last_price"]
                ),
            )
            for contract in contracts
        ]


option_chain_service = OptionChainService(instrument_lookup_service)
