from datetime import date

from app.market_data.instrument_lookup import InstrumentLookupService
from tests.market_data.fakes import FakeMarketDataClient

_RAW_INSTRUMENTS = [
    {
        "instrument_token": 1001,
        "tradingsymbol": "NIFTY26JUL24800CE",
        "name": "NIFTY",
        "expiry": date(2026, 7, 30),
        "strike": 24800.0,
        "instrument_type": "CE",
        "lot_size": 75,
    },
    {
        "instrument_token": 1002,
        "tradingsymbol": "NIFTY26JUL24800PE",
        "name": "NIFTY",
        "expiry": date(2026, 7, 30),
        "strike": 24800.0,
        "instrument_type": "PE",
        "lot_size": 75,
    },
    {
        "instrument_token": 1003,
        "tradingsymbol": "NIFTY26AUG24800CE",
        "name": "NIFTY",
        "expiry": date(2026, 8, 6),
        "strike": 24800.0,
        "instrument_type": "CE",
        "lot_size": 75,
    },
    {
        # Equities have no expiry - Kite returns an empty string, not null.
        "instrument_token": 2001,
        "tradingsymbol": "RELIANCE",
        "name": "RELIANCE",
        "expiry": "",
        "strike": 0.0,
        "instrument_type": "EQ",
        "lot_size": 1,
    },
]


def test_get_instruments_parses_raw_rows() -> None:
    client = FakeMarketDataClient(instruments=_RAW_INSTRUMENTS)
    service = InstrumentLookupService()

    instruments = service.get_instruments(client, "NFO")

    assert len(instruments) == 4
    assert instruments[0].instrument_token == 1001
    assert instruments[0].expiry == date(2026, 7, 30)
    assert instruments[3].expiry is None


def test_get_instruments_caches_within_the_same_day() -> None:
    client = FakeMarketDataClient(instruments=_RAW_INSTRUMENTS)
    service = InstrumentLookupService()

    service.get_instruments(client, "NFO")
    service.get_instruments(client, "NFO")
    service.get_instruments(client, "NFO")

    assert client.instrument_fetch_count == 1


def test_get_instruments_caches_separately_per_exchange() -> None:
    client = FakeMarketDataClient(instruments=_RAW_INSTRUMENTS)
    service = InstrumentLookupService()

    service.get_instruments(client, "NFO")
    service.get_instruments(client, "NSE")

    assert client.instrument_fetch_count == 2


def test_find_option_matches_exact_contract() -> None:
    client = FakeMarketDataClient(instruments=_RAW_INSTRUMENTS)
    service = InstrumentLookupService()

    found = service.find_option(
        client,
        underlying="NIFTY",
        strike=24800.0,
        option_type="PE",
        expiry=date(2026, 7, 30),
    )

    assert found is not None
    assert found.trading_symbol == "NIFTY26JUL24800PE"


def test_find_option_returns_none_when_no_match() -> None:
    client = FakeMarketDataClient(instruments=_RAW_INSTRUMENTS)
    service = InstrumentLookupService()

    found = service.find_option(
        client,
        underlying="NIFTY",
        strike=99999.0,
        option_type="CE",
        expiry=date(2026, 7, 30),
    )

    assert found is None


def test_get_expiries_returns_sorted_unique_dates_for_underlying() -> None:
    client = FakeMarketDataClient(instruments=_RAW_INSTRUMENTS)
    service = InstrumentLookupService()

    expiries = service.get_expiries(client, "NIFTY")

    assert expiries == [date(2026, 7, 30), date(2026, 8, 6)]
