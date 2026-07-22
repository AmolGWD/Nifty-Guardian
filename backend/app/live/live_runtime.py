"""
`start_live_runtime()`: wires the Runtime Engine (`app.runtime`,
frozen) + a Live Market Feed (this package) + a broker adapter
(`app.brokers.ZerodhaBroker`, or `PaperBroker` for a dry run - both
frozen) together. Introduces NO new strategy logic - every candle is
still processed by the exact same frozen `EventProcessor` every other
phase already uses; this module only wires existing pieces together
plus this phase's own safety/heartbeat/reconnect layer.

Mirrors `app.runtime.startup.start_runtime()`'s own wiring order
exactly (Event Bus -> Managers -> Broker -> Portfolio -> Runtime
Engine), the same reason `app.api.dashboard.dashboard_service`
(Phase 22) didn't call `start_runtime()` directly: this module also
needs to inject its own broker (`OrderExecutor`, wrapping whatever
`BrokerInterface` implementation the caller provides) in place of a
plain `PaperBroker`, another constructor argument `start_runtime()`
doesn't expose.

One documented, deliberate type-hint mismatch, not a real one:
`EventProcessor.__init__`'s `broker` parameter is typed concretely as
`PaperBroker` (frozen, `app.runtime.event_processor`), not the
`BrokerInterface` Protocol it structurally needs. `OrderExecutor`
satisfies `BrokerInterface` exactly the way `PaperBroker`/
`ZerodhaBroker` already do (same two methods, same signatures) - the
`# type: ignore[arg-type]` below is scoped to this one line, not a
suppression of a real bug, and is the safer choice over editing the
frozen `app.runtime` package for what is, at runtime, a correct,
Protocol-satisfying substitution.
"""

from dataclasses import dataclass

from app.live.heartbeat import HeartbeatMonitor
from app.live.live_market_feed import LiveFeedMarketDataSource, LiveMarketFeedInterface
from app.live.live_session import LiveSession
from app.live.models import LiveConfig
from app.live.order_executor import OrderExecutor
from app.live.reconnect import ReconnectManager, ReconnectPolicy
from app.live.safety_manager import SafetyManager
from app.paper_trading.broker_interface import BrokerInterface
from app.paper_trading.event_bus import EventBus
from app.paper_trading.execution_journal import ExecutionJournal
from app.paper_trading.order_manager import OrderManager
from app.paper_trading.performance_monitor import PerformanceMonitor
from app.paper_trading.portfolio_manager import PortfolioManager
from app.paper_trading.position_manager import PositionManager
from app.runtime.engine_config import EngineConfig
from app.runtime.event_processor import EventProcessor
from app.runtime.health import HealthMonitor
from app.runtime.runtime_engine import RuntimeEngine
from app.runtime.scheduler import SynchronousScheduler
from app.runtime.session_controller import SessionController
from app.trading.risk.models import RiskConfig
from app.trading.strategy.registry import StrategyRegistry, default_registry


@dataclass
class LiveRuntimeContext:
    live_session: LiveSession
    order_executor: OrderExecutor
    safety_manager: SafetyManager
    heartbeat_monitor: HeartbeatMonitor
    reconnect_manager: ReconnectManager
    runtime_engine: RuntimeEngine
    session_controller: SessionController
    event_bus: EventBus
    order_manager: OrderManager
    position_manager: PositionManager
    portfolio_manager: PortfolioManager
    execution_journal: ExecutionJournal
    performance_monitor: PerformanceMonitor
    health_monitor: HealthMonitor
    market_feed: LiveMarketFeedInterface


def start_live_runtime(
    *,
    market_feed: LiveMarketFeedInterface,
    broker: BrokerInterface,
    expected_candle_count: int,
    config: LiveConfig,
    initial_capital: float = 100_000.0,
    risk_config: RiskConfig | None = None,
    strategy_registry: StrategyRegistry | None = None,
    warmup_candles: int = 20,
    engine_config: EngineConfig | None = None,
) -> LiveRuntimeContext:
    order_executor = OrderExecutor(broker)

    event_bus = EventBus()
    position_manager = PositionManager(event_bus)
    portfolio_manager = PortfolioManager(
        initial_cash=initial_capital, position_manager=position_manager, event_bus=event_bus
    )
    order_manager = OrderManager(event_bus)

    session_controller = SessionController()
    execution_journal = ExecutionJournal()
    execution_journal.subscribe_to(event_bus)
    performance_monitor = PerformanceMonitor(event_bus, initial_capital=initial_capital)
    health_monitor = HealthMonitor(event_bus, session_controller)

    event_processor = EventProcessor(
        event_bus=event_bus,
        order_manager=order_manager,
        position_manager=position_manager,
        portfolio_manager=portfolio_manager,
        broker=order_executor,  # type: ignore[arg-type]  # see module docstring
        strategy_registry=strategy_registry or default_registry(),
        risk_config=risk_config or RiskConfig(),
        initial_capital=initial_capital,
        warmup_candles=warmup_candles,
    )

    market_data_source = LiveFeedMarketDataSource(
        market_feed, expected_length=expected_candle_count
    )

    runtime_engine = RuntimeEngine(
        config=engine_config or EngineConfig(),
        market_data_source=market_data_source,
        event_processor=event_processor,
        session_controller=session_controller,
        scheduler=SynchronousScheduler(),
        health_monitor=health_monitor,
    )

    safety_manager = SafetyManager(config)
    heartbeat_monitor = HeartbeatMonitor(interval_seconds=config.heartbeat_interval_seconds)
    reconnect_manager = ReconnectManager(ReconnectPolicy(max_retries=config.reconnect_limit))

    live_session = LiveSession(
        market_feed=market_feed,
        safety_manager=safety_manager,
        heartbeat_monitor=heartbeat_monitor,
        reconnect_manager=reconnect_manager,
    )

    return LiveRuntimeContext(
        live_session=live_session,
        order_executor=order_executor,
        safety_manager=safety_manager,
        heartbeat_monitor=heartbeat_monitor,
        reconnect_manager=reconnect_manager,
        runtime_engine=runtime_engine,
        session_controller=session_controller,
        event_bus=event_bus,
        order_manager=order_manager,
        position_manager=position_manager,
        portfolio_manager=portfolio_manager,
        execution_journal=execution_journal,
        performance_monitor=performance_monitor,
        health_monitor=health_monitor,
        market_feed=market_feed,
    )
