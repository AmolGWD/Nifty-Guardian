from datetime import datetime

from app.trading.conditions.cooldown import is_cooldown_complete


def test_cooldown_complete_when_no_last_trade_supplied() -> None:
    timestamp = datetime(2026, 7, 21, 11, 0)
    assert is_cooldown_complete(timestamp, None, 5) is True


def test_cooldown_not_complete_immediately_after_close() -> None:
    current = datetime(2026, 7, 21, 11, 0)
    last_closed = datetime(2026, 7, 21, 10, 57)
    assert is_cooldown_complete(current, last_closed, 5) is False


def test_cooldown_complete_at_exact_boundary() -> None:
    current = datetime(2026, 7, 21, 11, 0)
    last_closed = datetime(2026, 7, 21, 10, 55)
    assert is_cooldown_complete(current, last_closed, 5) is True


def test_cooldown_complete_well_after_period() -> None:
    current = datetime(2026, 7, 21, 11, 30)
    last_closed = datetime(2026, 7, 21, 10, 0)
    assert is_cooldown_complete(current, last_closed, 5) is True
