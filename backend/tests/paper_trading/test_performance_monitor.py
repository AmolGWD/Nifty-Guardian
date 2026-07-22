import pytest

from app.paper_trading.event_bus import EventBus
from app.paper_trading.order_manager import OrderManager
from app.paper_trading.paper_broker import PaperBroker
from app.paper_trading.performance_monitor import PerformanceMonitor
from app.paper_trading.portfolio_manager import PortfolioManager
from app.paper_trading.position_manager import PositionManager
from app.trading.strategy.models import StrategyDirection
from tests.paper_trading.helpers import make_order


def test_initial_snapshot_is_all_zero() -> None:
    bus = EventBus()
    monitor = PerformanceMonitor(bus, initial_capital=100_000.0)

    snapshot = monitor.snapshot()

    assert snapshot.orders_submitted == 0
    assert snapshot.orders_filled == 0
    assert snapshot.orders_rejected == 0
    assert snapshot.orders_cancelled == 0
    assert snapshot.fill_ratio_percent == 0.0
    assert snapshot.win_rate_percent == 0.0
    assert snapshot.average_execution_latency_seconds is None


def test_tracks_submitted_and_filled_orders() -> None:
    bus = EventBus()
    monitor = PerformanceMonitor(bus, initial_capital=100_000.0)
    manager = OrderManager(bus)

    order = make_order(manager)
    manager.validate(order.order_id)
    manager.submit(order.order_id, PaperBroker())

    snapshot = monitor.snapshot()
    assert snapshot.orders_submitted == 1
    assert snapshot.orders_filled == 1
    assert snapshot.fill_ratio_percent == pytest.approx(100.0)
    assert snapshot.average_execution_latency_seconds is not None
    assert snapshot.average_execution_latency_seconds >= 0.0


def test_tracks_rejected_orders() -> None:
    bus = EventBus()
    monitor = PerformanceMonitor(bus, initial_capital=100_000.0)
    manager = OrderManager(bus)

    order = make_order(manager)
    manager.reject(order.order_id, "test")

    snapshot = monitor.snapshot()
    assert snapshot.orders_rejected == 1


def test_win_rate_from_closed_positions() -> None:
    bus = EventBus()
    monitor = PerformanceMonitor(bus, initial_capital=100_000.0)
    position_manager = PositionManager(bus)

    winner = position_manager.open_position(
        strategy_name="EMABreakout", direction=StrategyDirection.LONG,
        entry_price=100.0, quantity=10,
    )
    position_manager.exit(winner.position_id, exit_quantity=10, exit_price=110.0)

    loser = position_manager.open_position(
        strategy_name="EMABreakout", direction=StrategyDirection.LONG,
        entry_price=100.0, quantity=10,
    )
    position_manager.exit(loser.position_id, exit_quantity=10, exit_price=95.0)

    snapshot = monitor.snapshot()
    assert snapshot.win_rate_percent == pytest.approx(50.0)


def test_daily_return_and_max_drawdown_from_portfolio_events() -> None:
    bus = EventBus()
    monitor = PerformanceMonitor(bus, initial_capital=100_000.0)
    position_manager = PositionManager(bus)
    portfolio_manager = PortfolioManager(
        initial_cash=100_000.0, position_manager=position_manager, event_bus=bus
    )

    position = position_manager.open_position(
        strategy_name="EMABreakout", direction=StrategyDirection.LONG,
        entry_price=100.0, quantity=10,
    )
    position_manager.update_unrealized_pnl(position.position_id, 110.0)
    portfolio_manager.snapshot()

    position_manager.update_unrealized_pnl(position.position_id, 95.0)
    portfolio_manager.snapshot()

    snapshot = monitor.snapshot()
    assert snapshot.max_drawdown == pytest.approx(150.0)
