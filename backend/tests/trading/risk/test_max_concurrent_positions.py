from app.trading.risk.max_concurrent_positions import is_within_max_concurrent_positions


def test_within_limit_when_no_open_positions() -> None:
    assert is_within_max_concurrent_positions(0, 1) is True


def test_not_within_limit_at_exact_maximum() -> None:
    assert is_within_max_concurrent_positions(1, 1) is False


def test_within_limit_below_a_higher_maximum() -> None:
    assert is_within_max_concurrent_positions(2, 3) is True
