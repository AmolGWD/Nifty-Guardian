from datetime import date, datetime

from app.trading.conditions.expiry_day_filter import is_expiry_allowed


def test_expiry_allowed_when_no_expiry_date_given() -> None:
    timestamp = datetime(2026, 7, 30, 11, 0)
    assert is_expiry_allowed(timestamp, None, allow_expiry_day_trading=False) is True


def test_expiry_allowed_on_non_expiry_day() -> None:
    timestamp = datetime(2026, 7, 21, 11, 0)  # Tuesday, not expiry
    assert is_expiry_allowed(
        timestamp, date(2026, 7, 30), allow_expiry_day_trading=False
    ) is True


def test_expiry_blocked_on_expiry_day_when_disallowed() -> None:
    timestamp = datetime(2026, 7, 30, 11, 0)  # Thursday, expiry day
    assert is_expiry_allowed(
        timestamp, date(2026, 7, 30), allow_expiry_day_trading=False
    ) is False


def test_expiry_allowed_on_expiry_day_when_allowed() -> None:
    timestamp = datetime(2026, 7, 30, 11, 0)  # Thursday, expiry day
    assert is_expiry_allowed(
        timestamp, date(2026, 7, 30), allow_expiry_day_trading=True
    ) is True
