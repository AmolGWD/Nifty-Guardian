from app.trading.conditions.gap_filter import is_gap_filter_ok


def test_gap_filter_ok_when_no_gap_supplied() -> None:
    assert is_gap_filter_ok(None, 1.0) is True


def test_gap_filter_ok_when_within_threshold() -> None:
    assert is_gap_filter_ok(0.5, 1.0) is True


def test_gap_filter_ok_at_exact_threshold() -> None:
    assert is_gap_filter_ok(1.0, 1.0) is True


def test_gap_filter_blocks_when_gap_exceeds_threshold() -> None:
    assert is_gap_filter_ok(1.5, 1.0) is False


def test_gap_filter_blocks_on_large_negative_gap() -> None:
    assert is_gap_filter_ok(-2.0, 1.0) is False
