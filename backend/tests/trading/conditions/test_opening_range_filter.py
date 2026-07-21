from datetime import datetime

from app.trading.conditions.opening_range_filter import is_opening_range_complete


def test_opening_range_not_complete_right_at_open() -> None:
    timestamp = datetime(2026, 7, 21, 9, 15)
    assert is_opening_range_complete(timestamp, "09:15", 15) is False


def test_opening_range_not_complete_one_minute_before_end() -> None:
    timestamp = datetime(2026, 7, 21, 9, 29)
    assert is_opening_range_complete(timestamp, "09:15", 15) is False


def test_opening_range_complete_exactly_at_boundary() -> None:
    timestamp = datetime(2026, 7, 21, 9, 30)
    assert is_opening_range_complete(timestamp, "09:15", 15) is True


def test_opening_range_complete_well_after_open() -> None:
    timestamp = datetime(2026, 7, 21, 11, 0)
    assert is_opening_range_complete(timestamp, "09:15", 15) is True
