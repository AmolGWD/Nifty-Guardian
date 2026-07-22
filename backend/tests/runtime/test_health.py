import pytest

from app.paper_trading.event_bus import EventBus
from app.paper_trading.order_manager import OrderManager
from app.paper_trading.paper_broker import PaperBroker
from app.paper_trading.portfolio_manager import PortfolioManager
from app.paper_trading.position_manager import PositionManager
from app.runtime.health import HealthMonitor
from app.runtime.session_controller import SessionController, SessionState
from app.trading.strategy.models import StrategyDirection
from tests.paper_trading.helpers import make_order


def test_initial_snapshot_is_all_zero() -> None:
    bus = EventBus()
    controller = SessionController()
    monitor = HealthMonitor(bus, controller)

    snapshot = monitor.snapshot()
    assert snapshot.processed_candles == 0
    assert snapshot.average_processing_latency_seconds is None
    assert snapshot.events_published == 0
    assert snapshot.orders_generated == 0
    assert snapshot.current_state == SessionState.NOT_STARTED
    assert snapshot.uptime_seconds >= 0.0


def test_record_candle_processed_tracks_count_and_average_latency() -> None:
    monitor = HealthMonitor(EventBus(), SessionController())
    monitor.record_candle_processed(0.10)
    monitor.record_candle_processed(0.20)
    monitor.record_candle_processed(0.30)

    snapshot = monitor.snapshot()
    assert snapshot.processed_candles == 3
    assert snapshot.average_processing_latency_seconds == pytest.approx(0.20)


def test_current_state_reflects_session_controller_live() -> None:
    controller = SessionController()
    monitor = HealthMonitor(EventBus(), controller)

    controller.start()
    assert monitor.snapshot().current_state == SessionState.RUNNING
    controller.pause()
    assert monitor.snapshot().current_state == SessionState.PAUSED


def test_events_published_counts_every_subscribed_event_type() -> None:
    bus = EventBus()
    monitor = HealthMonitor(bus, SessionController())
    order_manager = OrderManager(bus)
    broker = PaperBroker()

    order = make_order(order_manager)
    order_manager.validate(order.order_id)
    order_manager.submit(order.order_id, broker)  # publishes Submitted + Filled

    snapshot = monitor.snapshot()
    assert snapshot.events_published == 2


def test_orders_generated_counts_only_order_submitted_events() -> None:
    bus = EventBus()
    monitor = HealthMonitor(bus, SessionController())
    order_manager = OrderManager(bus)
    broker = PaperBroker()

    for _ in range(3):
        order = make_order(order_manager)
        order_manager.validate(order.order_id)
        order_manager.submit(order.order_id, broker)

    assert monitor.snapshot().orders_generated == 3


def test_position_and_portfolio_events_are_also_counted() -> None:
    bus = EventBus()
    monitor = HealthMonitor(bus, SessionController())
    position_manager = PositionManager(bus)
    portfolio_manager = PortfolioManager(
        initial_cash=100_000.0, position_manager=position_manager, event_bus=bus
    )

    position_manager.open_position(
        strategy_name="EMABreakout",
        direction=StrategyDirection.LONG,
        entry_price=100.0,
        quantity=10,
    )
    portfolio_manager.snapshot()

    snapshot = monitor.snapshot()
    assert snapshot.events_published >= 2  # PositionUpdated + PortfolioUpdated
