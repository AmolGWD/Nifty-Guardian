from datetime import date, datetime

import pytest

import app.market_data.expiry as expiry_module
from app.market_data.expiry import ExpiryDiscoveryService
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
        "instrument_token": 1003,
        "tradingsymbol": "NIFTY26AUG24800CE",
        "name": "NIFTY",
        "expiry": date(2026, 8, 6),
        "strike": 24800.0,
        "instrument_type": "CE",
        "lot_size": 75,
    },
]


def test_get_available_expiries_delegates_to_instrument_lookup() -> None:
    client = FakeMarketDataClient(instruments=_RAW_INSTRUMENTS)
    service = ExpiryDiscoveryService(InstrumentLookupService())

    expiries = service.get_available_expiries(client, "NIFTY")

    assert expiries == [date(2026, 7, 30), date(2026, 8, 6)]


def test_get_nearest_expiry_returns_earliest_upcoming() -> None:
    client = FakeMarketDataClient(instruments=_RAW_INSTRUMENTS)
    service = ExpiryDiscoveryService(InstrumentLookupService())

    nearest = service.get_nearest_expiry(client, "NIFTY")

    assert nearest == date(2026, 7, 30)


def test_get_nearest_expiry_skips_expiries_already_in_the_past(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class _FixedDatetime(datetime):
        @classmethod
        def now(cls, tz: object = None) -> datetime:  # type: ignore[override]
            return cls(2026, 8, 1)

    monkeypatch.setattr(expiry_module, "datetime", _FixedDatetime)

    client = FakeMarketDataClient(instruments=_RAW_INSTRUMENTS)
    service = ExpiryDiscoveryService(InstrumentLookupService())

    nearest = service.get_nearest_expiry(client, "NIFTY")

    assert nearest == date(2026, 8, 6)


def test_get_nearest_expiry_returns_none_when_no_expiries_available() -> None:
    client = FakeMarketDataClient(instruments=[])
    service = ExpiryDiscoveryService(InstrumentLookupService())

    assert service.get_nearest_expiry(client, "NIFTY") is None
