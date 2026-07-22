"""
Initializes every runtime component in the order the CTO brief names:
Event Bus, Managers, Paper Broker, Portfolio, Runtime Engine. Returns a
`RuntimeContext` bundling every wired instance - not a Pydantic model
(these are stateful services/managers, not immutable domain values),
just a plain container so callers (the demo script, tests) don't have
to repeat this wiring themselves.
"""

from dataclasses import dataclass

from app.paper_trading.event_bus import EventBus
from app.paper_trading.execution_journal import ExecutionJournal
from app.paper_trading.order_manager import OrderManager
from app.paper_trading.paper_broker import PaperBroker
from app.paper_trading.performance_monitor import PerformanceMonitor
from app.paper_trading.portfolio_manager import PortfolioManager
from app.paper_trading.position_manager import PositionManager
from app.runtime.engine_config import EngineConfig
from app.runtime.event_processor import EventProcessor
from app.runtime.health import HealthMonitor
from app.runtime.market_data_source import MarketDataSource
from app.runtime.runtime_engine import RuntimeEngine
from app.runtime.scheduler import SynchronousScheduler
from app.runtime.session_controller import SessionController
from app.trading.risk.models import RiskConfig
from app.trading.strategy.registry import StrategyRegistry, default_registry


@dataclass
class RuntimeContext:
    event_bus: EventBus
    order_manager: OrderManager
    position_manager: PositionManager
    portfolio_manager: PortfolioManager
    broker: PaperBroker
    execution_journal: ExecutionJournal
    performance_monitor: PerformanceMonitor
    health_monitor: HealthMonitor
    session_controller: SessionController
    event_processor: EventProcessor
    engine: RuntimeEngine


def start_runtime(
    *,
    config: EngineConfig,
    market_data_source: MarketDataSource,
    initial_capital: float = 100_000.0,
    risk_config: RiskConfig | None = None,
    strategy_registry: StrategyRegistry | None = None,
    warmup_candles: int = 20,
) -> RuntimeContext:
    # 1. Event Bus
    event_bus = EventBus()

    # 2. Managers
    position_manager = PositionManager(event_bus)
    portfolio_manager = PortfolioManager(
        initial_cash=initial_capital, position_manager=position_manager, event_bus=event_bus
    )
    order_manager = OrderManager(event_bus)

    # 3. Paper Broker
    broker = PaperBroker()

    # 4. Portfolio - already initialized above (PortfolioManager owns it); observers next.
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
        broker=broker,
        strategy_registry=strategy_registry or default_registry(),
        risk_config=risk_config or RiskConfig(),
        initial_capital=initial_capital,
        warmup_candles=warmup_candles,
    )

    # 5. Runtime Engine
    engine = RuntimeEngine(
        config=config,
        market_data_source=market_data_source,
        event_processor=event_processor,
        session_controller=session_controller,
        scheduler=SynchronousScheduler(),
        health_monitor=health_monitor,
    )

    return RuntimeContext(
        event_bus=event_bus,
        order_manager=order_manager,
        position_manager=position_manager,
        portfolio_manager=portfolio_manager,
        broker=broker,
        execution_journal=execution_journal,
        performance_monitor=performance_monitor,
        health_monitor=health_monitor,
        session_controller=session_controller,
        event_processor=event_processor,
        engine=engine,
    )
