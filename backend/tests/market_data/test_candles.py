from datetime import datetime

from app.market_data.candles import CandleService
from tests.market_data.fakes import FakeMarketDataClient


def test_get_candles_normalizes_ohlcv() -> None:
    client = FakeMarketDataClient(
        historical_data=[
            {
                "date": datetime(2026, 7, 20, 9, 15),
                "open": 24700.0,
                "high": 24750.0,
                "low": 24690.0,
                "close": 24720.0,
                "volume": 12345,
            },
            {
                "date": datetime(2026, 7, 20, 9, 30),
                "open": 24720.0,
                "high": 24780.0,
                "low": 24710.0,
                "close": 24760.0,
                "volume": 9876,
            },
        ]
    )
    service = CandleService()

    candles = service.get_candles(
        client,
        instrument_token=256265,
        from_date=datetime(2026, 7, 20),
        to_date=datetime(2026, 7, 21),
        interval="15minute",
    )

    assert len(candles) == 2
    assert candles[0].open == 24700.0
    assert candles[0].close == 24720.0
    assert candles[1].volume == 9876


def test_get_candles_returns_empty_list_when_no_data() -> None:
    client = FakeMarketDataClient(historical_data=[])
    service = CandleService()

    candles = service.get_candles(
        client,
        instrument_token=256265,
        from_date=datetime(2026, 7, 20),
        to_date=datetime(2026, 7, 21),
        interval="day",
    )

    assert candles == []
