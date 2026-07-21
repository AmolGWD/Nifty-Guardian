from app.trading.risk.target import calculate_target
from app.trading.strategy.models import StrategyDirection


def test_target_above_entry_when_long() -> None:
    assert calculate_target(100.0, 2.0, 3.0, StrategyDirection.LONG) == 106.0


def test_target_below_entry_when_short() -> None:
    assert calculate_target(100.0, 2.0, 3.0, StrategyDirection.SHORT) == 94.0


def test_target_equals_entry_when_no_direction() -> None:
    assert calculate_target(100.0, 2.0, 3.0, StrategyDirection.NONE) == 100.0
