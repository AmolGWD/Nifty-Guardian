"""
`start_signal_engine()`: wires `SignalService` onto an already-built
`app.live.live_runtime.LiveRuntimeContext` (Phase 24, frozen) - not a
new orchestration layer, just one more subscriber on the exact same
public `event_bus` `ExecutionJournal`/`PerformanceMonitor` already
attach to inside `start_live_runtime()` itself. Zero changes to any
frozen file: `LiveRuntimeContext.event_bus` was already a public field.

The broker passed to `start_live_runtime()` should always be a
`PaperBroker` here - this package creates dummy (paper) trades only,
never a real order, never a real broker. Passing a real
`ZerodhaBroker` would still work mechanically (both satisfy the same
`BrokerInterface`) but would defeat the entire point of "dummy trade
tracking, no automated order placement" this phase exists to deliver -
callers are expected to always pass a `PaperBroker`.
"""

from dataclasses import dataclass
from pathlib import Path

from app.live.live_market_feed import LiveMarketFeedInterface
from app.live.live_runtime import LiveRuntimeContext, start_live_runtime
from app.live.models import LiveConfig
from app.paper_trading.broker_interface import BrokerInterface
from app.runtime.engine_config import EngineConfig
from app.signals.models import SignalConfig
from app.signals.signal_service import NotificationSink, SignalService
from app.trading.risk.models import RiskConfig
from app.trading.strategy.registry import StrategyRegistry


@dataclass
class SignalEngineContext:
    live_context: LiveRuntimeContext
    signal_service: SignalService


def start_signal_engine(
    *,
    market_feed: LiveMarketFeedInterface,
    broker: BrokerInterface,
    expected_candle_count: int,
    live_config: LiveConfig,
    signal_config: SignalConfig,
    notification_service: NotificationSink,
    initial_capital: float = 100_000.0,
    risk_config: RiskConfig | None = None,
    strategy_registry: StrategyRegistry | None = None,
    warmup_candles: int = 20,
    engine_config: EngineConfig | None = None,
    reports_directory: Path | None = None,
) -> SignalEngineContext:
    live_context = start_live_runtime(
        market_feed=market_feed,
        broker=broker,
        expected_candle_count=expected_candle_count,
        config=live_config,
        initial_capital=initial_capital,
        risk_config=risk_config,
        strategy_registry=strategy_registry,
        warmup_candles=warmup_candles,
        engine_config=engine_config,
    )

    signal_service = SignalService(
        config=signal_config,
        notification_service=notification_service,
        reports_directory=reports_directory,
    )
    signal_service.subscribe_to(live_context.event_bus)

    return SignalEngineContext(live_context=live_context, signal_service=signal_service)
