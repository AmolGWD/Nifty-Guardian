import pytest

from app.paper_trading.event_bus import EventBus
from app.paper_trading.events import PositionUpdatedEvent
from app.paper_trading.models import PositionStatus
from app.paper_trading.position_manager import PositionManager
from app.trading.strategy.models import StrategyDirection


def test_open_position_starts_open_with_zero_pnl() -> None:
    manager = PositionManager(EventBus())
    position = manager.open_position(
        strategy_name="EMABreakout", direction=StrategyDirection.LONG,
        entry_price=100.0, quantity=10,
    )

    assert position.status == PositionStatus.OPEN
    assert position.realized_pnl == 0.0
    assert position.unrealized_pnl == 0.0
    assert position.quantity == 10


def test_update_unrealized_pnl_for_long_position() -> None:
    manager = PositionManager(EventBus())
    position = manager.open_position(
        strategy_name="EMABreakout", direction=StrategyDirection.LONG,
        entry_price=100.0, quantity=10,
    )

    updated = manager.update_unrealized_pnl(position.position_id, 105.0)

    assert updated.unrealized_pnl == pytest.approx(50.0)


def test_update_unrealized_pnl_for_short_position() -> None:
    manager = PositionManager(EventBus())
    position = manager.open_position(
        strategy_name="EMABreakout", direction=StrategyDirection.SHORT,
        entry_price=100.0, quantity=10,
    )

    updated = manager.update_unrealized_pnl(position.position_id, 90.0)

    assert updated.unrealized_pnl == pytest.approx(100.0)


def test_full_exit_closes_the_position() -> None:
    manager = PositionManager(EventBus())
    position = manager.open_position(
        strategy_name="EMABreakout", direction=StrategyDirection.LONG,
        entry_price=100.0, quantity=10,
    )

    closed = manager.exit(position.position_id, exit_quantity=10, exit_price=110.0)

    assert closed.status == PositionStatus.CLOSED
    assert closed.quantity == 0
    assert closed.realized_pnl == pytest.approx(100.0)
    assert closed.closed_at is not None


def test_partial_exit_reduces_quantity_and_keeps_position_open() -> None:
    manager = PositionManager(EventBus())
    position = manager.open_position(
        strategy_name="EMABreakout", direction=StrategyDirection.LONG,
        entry_price=100.0, quantity=10,
    )

    partial = manager.exit(position.position_id, exit_quantity=4, exit_price=110.0)

    assert partial.status == PositionStatus.PARTIALLY_EXITED
    assert partial.quantity == 6
    assert partial.realized_pnl == pytest.approx(40.0)


def test_sequential_partial_exits_accumulate_realized_pnl() -> None:
    manager = PositionManager(EventBus())
    position = manager.open_position(
        strategy_name="EMABreakout", direction=StrategyDirection.LONG,
        entry_price=100.0, quantity=10,
    )

    manager.exit(position.position_id, exit_quantity=4, exit_price=110.0)
    final = manager.exit(position.position_id, exit_quantity=6, exit_price=120.0)

    assert final.status == PositionStatus.CLOSED
    assert final.realized_pnl == pytest.approx(4 * 10 + 6 * 20)


def test_exit_more_than_remaining_quantity_raises() -> None:
    manager = PositionManager(EventBus())
    position = manager.open_position(
        strategy_name="EMABreakout", direction=StrategyDirection.LONG,
        entry_price=100.0, quantity=10,
    )

    with pytest.raises(ValueError, match="exceeds remaining"):
        manager.exit(position.position_id, exit_quantity=20, exit_price=110.0)


def test_exit_a_closed_position_raises() -> None:
    manager = PositionManager(EventBus())
    position = manager.open_position(
        strategy_name="EMABreakout", direction=StrategyDirection.LONG,
        entry_price=100.0, quantity=10,
    )
    manager.exit(position.position_id, exit_quantity=10, exit_price=110.0)

    with pytest.raises(ValueError, match="already-closed"):
        manager.exit(position.position_id, exit_quantity=1, exit_price=100.0)


def test_update_unrealized_pnl_on_closed_position_raises() -> None:
    manager = PositionManager(EventBus())
    position = manager.open_position(
        strategy_name="EMABreakout", direction=StrategyDirection.LONG,
        entry_price=100.0, quantity=10,
    )
    manager.exit(position.position_id, exit_quantity=10, exit_price=110.0)

    with pytest.raises(ValueError, match="closed"):
        manager.update_unrealized_pnl(position.position_id, 120.0)


def test_open_positions_excludes_closed() -> None:
    manager = PositionManager(EventBus())
    open_one = manager.open_position(
        strategy_name="EMABreakout", direction=StrategyDirection.LONG,
        entry_price=100.0, quantity=10,
    )
    closed_one = manager.open_position(
        strategy_name="EMABreakout", direction=StrategyDirection.LONG,
        entry_price=100.0, quantity=5,
    )
    manager.exit(closed_one.position_id, exit_quantity=5, exit_price=110.0)

    open_ids = {p.position_id for p in manager.open_positions()}
    closed_ids = {p.position_id for p in manager.closed_positions()}

    assert open_ids == {open_one.position_id}
    assert closed_ids == {closed_one.position_id}


def test_every_mutation_publishes_position_updated() -> None:
    bus = EventBus()
    published: list[PositionUpdatedEvent] = []
    bus.subscribe(PositionUpdatedEvent, published.append)

    manager = PositionManager(bus)
    position = manager.open_position(
        strategy_name="EMABreakout", direction=StrategyDirection.LONG,
        entry_price=100.0, quantity=10,
    )
    manager.update_unrealized_pnl(position.position_id, 105.0)
    manager.exit(position.position_id, exit_quantity=10, exit_price=110.0)

    assert len(published) == 3
