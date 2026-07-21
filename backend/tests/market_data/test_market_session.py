from datetime import datetime
from zoneinfo import ZoneInfo

from app.market_data.market_session import MarketSessionService, MarketSessionStatus

IST = ZoneInfo("Asia/Kolkata")


def test_pre_market_before_open() -> None:
    service = MarketSessionService()

    status = service.get_status(datetime(2026, 7, 20, 8, 0, tzinfo=IST))

    assert status == MarketSessionStatus.PRE_MARKET
    assert not service.is_open(datetime(2026, 7, 20, 8, 0, tzinfo=IST))


def test_open_during_market_hours() -> None:
    service = MarketSessionService()

    status = service.get_status(datetime(2026, 7, 20, 12, 0, tzinfo=IST))

    assert status == MarketSessionStatus.OPEN
    assert service.is_open(datetime(2026, 7, 20, 12, 0, tzinfo=IST))


def test_closed_after_market_hours() -> None:
    service = MarketSessionService()

    status = service.get_status(datetime(2026, 7, 20, 16, 0, tzinfo=IST))

    assert status == MarketSessionStatus.CLOSED
    assert not service.is_open(datetime(2026, 7, 20, 16, 0, tzinfo=IST))


def test_open_at_exact_boundaries() -> None:
    service = MarketSessionService()

    assert service.get_status(datetime(2026, 7, 20, 9, 15, tzinfo=IST)) == MarketSessionStatus.OPEN
    assert service.get_status(datetime(2026, 7, 20, 15, 30, tzinfo=IST)) == MarketSessionStatus.OPEN


def test_converts_non_ist_timezones() -> None:
    service = MarketSessionService()

    # 06:30 UTC = 12:00 IST - well inside market hours.
    utc_time = datetime(2026, 7, 20, 6, 30, tzinfo=ZoneInfo("UTC"))

    assert service.get_status(utc_time) == MarketSessionStatus.OPEN
