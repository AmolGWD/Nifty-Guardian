from datetime import date

from app.market_data.instrument_lookup import InstrumentLookupService
from app.market_data.option_chain import OptionChainService
from tests.market_data.fakes import FakeMarketDataClient

_EXPIRY = date(2026, 7, 30)

_RAW_INSTRUMENTS = [
    {
        "instrument_token": 1001,
        "tradingsymbol": "NIFTY26JUL24800CE",
        "name": "NIFTY",
        "expiry": _EXPIRY,
        "strike": 24800.0,
        "instrument_type": "CE",
        "lot_size": 75,
    },
    {
        "instrument_token": 1002,
        "tradingsymbol": "NIFTY26JUL24800PE",
        "name": "NIFTY",
        "expiry": _EXPIRY,
        "strike": 24800.0,
        "instrument_type": "PE",
        "lot_size": 75,
    },
    {
        # Different expiry - must not appear in the chain for _EXPIRY.
        "instrument_token": 1003,
        "tradingsymbol": "NIFTY26AUG24800CE",
        "name": "NIFTY",
        "expiry": date(2026, 8, 6),
        "strike": 24800.0,
        "instrument_type": "CE",
        "lot_size": 75,
    },
]

_LTP_RESPONSES = {
    "NFO:NIFTY26JUL24800CE": {"instrument_token": 1001, "last_price": 120.5},
    "NFO:NIFTY26JUL24800PE": {"instrument_token": 1002, "last_price": 95.25},
}


def test_get_option_chain_returns_only_matching_expiry_with_live_premiums() -> None:
    client = FakeMarketDataClient(instruments=_RAW_INSTRUMENTS, ltp_responses=_LTP_RESPONSES)
    service = OptionChainService(InstrumentLookupService())

    chain = service.get_option_chain(client, "NIFTY", _EXPIRY)

    assert len(chain) == 2
    by_symbol = {c.instrument.trading_symbol: c for c in chain}
    assert by_symbol["NIFTY26JUL24800CE"].last_price == 120.5
    assert by_symbol["NIFTY26JUL24800PE"].last_price == 95.25


def test_get_option_chain_returns_empty_list_when_no_contracts_match() -> None:
    client = FakeMarketDataClient(instruments=_RAW_INSTRUMENTS, ltp_responses=_LTP_RESPONSES)
    service = OptionChainService(InstrumentLookupService())

    chain = service.get_option_chain(client, "NIFTY", date(2099, 1, 1))

    assert chain == []
