from datetime import datetime

from app.market_data.market_session import MarketSessionStatus
from app.trading.conditions.session_validation import is_session_valid


def test_session_valid_on_open_weekday() -> None:
    timestamp = datetime(2026, 7, 21, 11, 0)  # Tuesday
    assert is_session_valid(MarketSessionStatus.OPEN, timestamp) is True


def test_session_invalid_when_session_state_not_open() -> None:
    timestamp = datetime(2026, 7, 21, 11, 0)  # Tuesday
    assert is_session_valid(MarketSessionStatus.CLOSED, timestamp) is False


def test_session_invalid_on_saturday() -> None:
    timestamp = datetime(2026, 7, 25, 11, 0)  # Saturday
    assert is_session_valid(MarketSessionStatus.OPEN, timestamp) is False


def test_session_invalid_on_sunday() -> None:
    timestamp = datetime(2026, 7, 26, 11, 0)  # Sunday
    assert is_session_valid(MarketSessionStatus.OPEN, timestamp) is False
