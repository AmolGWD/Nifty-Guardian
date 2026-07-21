from app.trading.risk.max_trades_per_day import is_within_max_trades_per_day


def test_within_limit_when_no_trades_taken_yet() -> None:
    assert is_within_max_trades_per_day(0, 5) is True


def test_within_limit_just_below_maximum() -> None:
    assert is_within_max_trades_per_day(4, 5) is True


def test_not_within_limit_at_exact_maximum() -> None:
    assert is_within_max_trades_per_day(5, 5) is False
