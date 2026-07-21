from app.trading.risk.daily_loss_limit import is_within_daily_loss_limit


def test_within_limit_when_no_loss_yet() -> None:
    assert is_within_daily_loss_limit(0.0, 5000.0) is True


def test_within_limit_just_below_maximum() -> None:
    assert is_within_daily_loss_limit(4999.0, 5000.0) is True


def test_not_within_limit_at_exact_maximum() -> None:
    assert is_within_daily_loss_limit(5000.0, 5000.0) is False


def test_not_within_limit_beyond_maximum() -> None:
    assert is_within_daily_loss_limit(6000.0, 5000.0) is False
