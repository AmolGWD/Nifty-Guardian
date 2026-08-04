"""
Owns the one live RuntimeContext this API process drives - wiring the
exact same components app.runtime.startup.start_runtime() wires, in
the same order (see docs/ENGINE_RUNTIME.md's "Startup sequence"), plus
one small addition of this API layer's own: an `_EventObserver`
subscribed to the event bus, since GET /api/dashboard needs to answer
"what was the most recent candle/signal/risk decision" and neither
EventProcessor nor any manager exposes that as public state - only as
transient events.

This module does not call start_runtime() directly because it needs
one constructor argument start_runtime() doesn't expose:
RuntimeEngine's candle_interval_seconds. The real default (900s / 15
minutes) is the correct value for realistic replay pacing but far too
slow for a human polling this REST API to watch progress in any
reasonable demo session - DEMO_CANDLE_INTERVAL_SECONDS below is this
API layer's own presentation-pacing choice, not a change to
app.runtime's real default (start_runtime() itself is untouched and
still uses 900s for any other caller).

Runs the engine on a background OS thread (RuntimeEngine.run() blocks
its calling thread inside a synchronous scheduler loop) - a hosting
choice this API layer makes, not a change to RuntimeEngine's own
synchronous design (docs/ENGINE_RUNTIME.md already documents this as
the exact seam an async host is expected to use later).
"""

import threading
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from app.api.dashboard.dashboard_models import (
    DashboardSnapshotResponse,
    PortfolioResponse,
    RuntimeStatsResponse,
)
from app.market_data.market_session import market_session_service
from app.market_data.schemas import Candle
from app.paper_trading.event_bus import EventBus
from app.paper_trading.events import (
    MarketDataReceivedEvent,
    RiskApprovedEvent,
    SignalGeneratedEvent,
)
from app.paper_trading.execution_journal import ExecutionJournal
from app.paper_trading.models import Portfolio as _PaperPortfolio
from app.paper_trading.order_manager import OrderManager
from app.paper_trading.paper_broker import PaperBroker
from app.paper_trading.performance_monitor import PerformanceMonitor, PerformanceSnapshot
from app.paper_trading.portfolio_manager import PortfolioManager
from app.paper_trading.position_manager import PositionManager
from app.runtime.engine_config import EngineConfig, ReplaySpeed
from app.runtime.event_processor import EventProcessor
from app.runtime.health import HealthMonitor, HealthSnapshot
from app.runtime.market_data_source import HistoricalReplaySource
from app.runtime.runtime_engine import RuntimeEngine
from app.runtime.scheduler import SynchronousScheduler
from app.runtime.session_controller import (
    InvalidSessionTransitionError,
    SessionController,
    SessionState,
)
from app.runtime.startup import RuntimeContext
from app.trading.context.engine import build_market_context
from app.trading.context.models import MarketContext
from app.trading.indicators.engine import calculate_indicator_snapshot
from app.trading.risk.models import RiskAssessment, RiskConfig
from app.trading.strategy.models import StrategyEvaluation
from app.trading.strategy.registry import default_registry

DEMO_CANDLE_INTERVAL_SECONDS = 2.0
INITIAL_CAPITAL = 100_000.0
WARMUP_CANDLES = 20

# Resolved relative to the `app` package root (parents[2] from this file:
# dashboard -> api -> app), not the repo root - so it still resolves
# correctly inside a container image that only ever copies `app/` (see
# `backend/Dockerfile`), regardless of the repo's own directory layout.
# This is the dataset's one canonical location - `scripts/`, which
# Railway's Docker build context (`backend/`) cannot reach, held a
# second copy until it was moved here to fix that exact deployment
# failure; local dev/demo scripts under `scripts/` reference this same
# path now (see e.g. `scripts/demo_backtest.py`).
_SAMPLE_DATASET_PATH = (
    Path(__file__).resolve().parents[2]
    / "market_data"
    / "sample_data"
    / "nifty_sample_candles.csv"
)


class DashboardConflictError(Exception):
    """Raised when a requested action conflicts with the current session state."""


class _EventObserver:
    """
    Tracks "the most recent X" purely by subscribing to the event bus -
    the same "learn everything from observation" discipline
    ExecutionJournal/PerformanceMonitor/HealthMonitor (frozen,
    app.paper_trading/app.runtime) already use; this is one more
    observer of the same bus, not a change to either package.
    """

    def __init__(self, event_bus: EventBus) -> None:
        self.last_candle: Candle | None = None
        self.candle_history: list[Candle] = []
        self.last_signal: StrategyEvaluation | None = None
        self.last_risk_decision: RiskAssessment | None = None

        event_bus.subscribe(MarketDataReceivedEvent, self._on_market_data)
        event_bus.subscribe(SignalGeneratedEvent, self._on_signal)
        event_bus.subscribe(RiskApprovedEvent, self._on_risk_approved)

    def _on_market_data(self, event: MarketDataReceivedEvent) -> None:
        self.last_candle = event.candle
        self.candle_history.append(event.candle)

    def _on_signal(self, event: SignalGeneratedEvent) -> None:
        self.last_signal = event.evaluation

    def _on_risk_approved(self, event: RiskApprovedEvent) -> None:
        self.last_risk_decision = event.risk_assessment

    def market_context(self) -> MarketContext | None:
        """
        Recomputed from the same frozen, pure classification functions
        EventProcessor itself calls (calculate_indicator_snapshot,
        build_market_context) with the same neutral OI inputs it uses
        (see app.runtime.event_processor) - a read-side projection for
        display, not a second decision-making pass: Market Context
        carries no signals/BUY-SELL/confidence (Phase 6's own scope).
        """
        if len(self.candle_history) <= WARMUP_CANDLES or self.last_candle is None:
            return None
        snapshot = calculate_indicator_snapshot(
            self.candle_history, total_call_oi=1, total_put_oi=1, price_change=0.0, oi_change=0.0
        )
        session_state = market_session_service.get_status(self.last_candle.timestamp)
        return build_market_context(snapshot, session_state)


@dataclass
class _RuntimeSession:
    context: RuntimeContext
    observer: _EventObserver
    config: EngineConfig
    total_candles: int
    thread: threading.Thread | None = None


def _build_empty_health() -> HealthSnapshot:
    return HealthSnapshot(
        processed_candles=0,
        average_processing_latency_seconds=None,
        uptime_seconds=0.0,
        events_published=0,
        orders_generated=0,
        current_state=SessionState.NOT_STARTED,
    )


def _build_empty_portfolio() -> PortfolioResponse:
    return PortfolioResponse(
        as_of=datetime.now(),
        cash=INITIAL_CAPITAL,
        available_margin=INITIAL_CAPITAL,
        open_position_ids=(),
        closed_position_ids=(),
        daily_pnl=0.0,
        total_equity=INITIAL_CAPITAL,
        peak_equity=INITIAL_CAPITAL,
    )


def _build_empty_performance() -> PerformanceSnapshot:
    return PerformanceMonitor(EventBus(), initial_capital=INITIAL_CAPITAL).snapshot()


def _to_portfolio_response(portfolio: _PaperPortfolio) -> PortfolioResponse:
    return PortfolioResponse(**portfolio.model_dump())


class DashboardRuntimeService:
    """The one live session this API process drives. See module docstring."""

    def __init__(self) -> None:
        self._session: _RuntimeSession | None = None
        self._lock = threading.Lock()

    def start(self) -> RuntimeStatsResponse:
        with self._lock:
            if self._session is not None:
                raise DashboardConflictError(
                    "cannot start: a session already exists "
                    f"(state={self._session.context.session_controller.state})"
                )
            self._session = self._build_session(
                config=EngineConfig(replay_speed=ReplaySpeed.X1), maximum_candles=None
            )
            self._spawn_thread(self._session)
            return self._runtime_stats_for(self._session)

    def pause(self) -> RuntimeStatsResponse:
        with self._lock:
            session = self._require_session()
            try:
                session.context.session_controller.pause()
            except InvalidSessionTransitionError as exc:
                raise DashboardConflictError(str(exc)) from exc
            return self._runtime_stats_for(session)

    def resume(self) -> RuntimeStatsResponse:
        with self._lock:
            session = self._require_session()
            if session.context.session_controller.state != SessionState.PAUSED:
                raise DashboardConflictError("cannot resume: session is not paused")
            self._spawn_thread(session)
            return self._runtime_stats_for(session)

    def stop(self) -> RuntimeStatsResponse:
        with self._lock:
            session = self._require_session()
            try:
                session.context.session_controller.stop()
            except InvalidSessionTransitionError as exc:
                raise DashboardConflictError(str(exc)) from exc
            return self._runtime_stats_for(session)

    def replay(
        self, *, replay_speed: ReplaySpeed, maximum_candles: int | None
    ) -> RuntimeStatsResponse:
        with self._lock:
            if self._session is not None:
                controller = self._session.context.session_controller
                if controller.state in (SessionState.RUNNING, SessionState.PAUSED):
                    controller.stop()
            self._session = self._build_session(
                config=EngineConfig(replay_speed=replay_speed), maximum_candles=maximum_candles
            )
            self._spawn_thread(self._session)
            return self._runtime_stats_for(self._session)

    def dashboard_snapshot(self) -> DashboardSnapshotResponse:
        with self._lock:
            session = self._session
        if session is None:
            return self._empty_snapshot()

        context = session.context
        observer = session.observer
        open_positions = context.position_manager.open_positions()
        closed_positions = context.position_manager.closed_positions()

        return DashboardSnapshotResponse(
            runtime=self._runtime_stats_for(session),
            current_candle=observer.last_candle,
            market_context=observer.market_context(),
            latest_signal=observer.last_signal,
            latest_risk_decision=observer.last_risk_decision,
            latest_recommendation=None,
            orders=list(context.order_manager.all_orders()),
            positions=list(open_positions) + list(closed_positions),
            portfolio=_to_portfolio_response(context.portfolio_manager.snapshot()),
            journal=list(context.execution_journal.all_entries()),
            health=context.health_monitor.snapshot(),
            performance=context.performance_monitor.snapshot(),
        )

    def health_snapshot(self) -> HealthSnapshot:
        with self._lock:
            session = self._session
        if session is None:
            return _build_empty_health()
        return session.context.health_monitor.snapshot()

    def runtime_state(self) -> SessionState:
        with self._lock:
            session = self._session
        if session is None:
            return SessionState.NOT_STARTED
        return session.context.session_controller.state

    # -- internals (caller already holds self._lock) --

    def _require_session(self) -> _RuntimeSession:
        if self._session is None:
            raise DashboardConflictError("no session has been started yet")
        return self._session

    def _build_session(
        self, *, config: EngineConfig, maximum_candles: int | None
    ) -> _RuntimeSession:
        market_data_source = HistoricalReplaySource(
            str(_SAMPLE_DATASET_PATH), maximum_candles=maximum_candles
        )

        event_bus = EventBus()
        observer = _EventObserver(event_bus)

        position_manager = PositionManager(event_bus)
        portfolio_manager = PortfolioManager(
            initial_cash=INITIAL_CAPITAL, position_manager=position_manager, event_bus=event_bus
        )
        order_manager = OrderManager(event_bus)
        broker = PaperBroker()

        session_controller = SessionController()
        execution_journal = ExecutionJournal()
        execution_journal.subscribe_to(event_bus)
        performance_monitor = PerformanceMonitor(event_bus, initial_capital=INITIAL_CAPITAL)
        health_monitor = HealthMonitor(event_bus, session_controller)

        event_processor = EventProcessor(
            event_bus=event_bus,
            order_manager=order_manager,
            position_manager=position_manager,
            portfolio_manager=portfolio_manager,
            broker=broker,
            strategy_registry=default_registry(),
            risk_config=RiskConfig(),
            initial_capital=INITIAL_CAPITAL,
            warmup_candles=WARMUP_CANDLES,
        )

        engine = RuntimeEngine(
            config=config,
            market_data_source=market_data_source,
            event_processor=event_processor,
            session_controller=session_controller,
            scheduler=SynchronousScheduler(),
            health_monitor=health_monitor,
            candle_interval_seconds=DEMO_CANDLE_INTERVAL_SECONDS,
        )

        context = RuntimeContext(
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

        return _RuntimeSession(
            context=context,
            observer=observer,
            config=config,
            total_candles=len(market_data_source),
        )

    def _spawn_thread(self, session: _RuntimeSession) -> None:
        thread = threading.Thread(target=session.context.engine.run, daemon=True)
        session.thread = thread
        thread.start()

    def _runtime_stats_for(self, session: _RuntimeSession) -> RuntimeStatsResponse:
        health = session.context.health_monitor.snapshot()
        return RuntimeStatsResponse(
            session_state=session.context.session_controller.state,
            replay_speed=session.config.replay_speed,
            processed_candles=session.context.engine.processed_count,
            total_candles=session.total_candles,
            events_published=health.events_published,
            orders_generated=health.orders_generated,
            uptime_seconds=health.uptime_seconds,
        )

    def _empty_snapshot(self) -> DashboardSnapshotResponse:
        return DashboardSnapshotResponse(
            runtime=RuntimeStatsResponse(
                session_state=SessionState.NOT_STARTED,
                replay_speed=ReplaySpeed.X1,
                processed_candles=0,
                total_candles=0,
                events_published=0,
                orders_generated=0,
                uptime_seconds=0.0,
            ),
            current_candle=None,
            market_context=None,
            latest_signal=None,
            latest_risk_decision=None,
            latest_recommendation=None,
            orders=[],
            positions=[],
            portfolio=_build_empty_portfolio(),
            journal=[],
            health=_build_empty_health(),
            performance=_build_empty_performance(),
        )


dashboard_runtime_service = DashboardRuntimeService()
