from app.trading.risk.stop_loss import calculate_stop_loss
from app.trading.strategy.models import StrategyDirection


def test_stop_loss_below_entry_when_long() -> None:
    assert calculate_stop_loss(100.0, 2.0, 1.5, StrategyDirection.LONG) == 97.0


def test_stop_loss_above_entry_when_short() -> None:
    assert calculate_stop_loss(100.0, 2.0, 1.5, StrategyDirection.SHORT) == 103.0


def test_stop_loss_equals_entry_when_no_direction() -> None:
    assert calculate_stop_loss(100.0, 2.0, 1.5, StrategyDirection.NONE) == 100.0
