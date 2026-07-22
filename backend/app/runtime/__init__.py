"""
Paper Trading Engine (Phase 20).

Orchestrates the existing, frozen platform - Indicators, Context,
Conditions, Strategy, Risk, Decision (Phases 5-10), and the Phase 19
event-driven paper trading pieces - into a single, replayable runtime
loop. No new trading logic: every decision this package makes is a
call into a package that already owns that decision. See
docs/ENGINE_RUNTIME.md for the full architecture and lifecycle.
"""

from app.runtime.engine_config import EngineConfig, ReplaySpeed, TradingSessionMode
from app.runtime.event_processor import EventProcessor
from app.runtime.health import HealthMonitor, HealthSnapshot
from app.runtime.market_data_source import (
    HistoricalReplaySource,
    MarketDataSource,
    StaticListSource,
)
from app.runtime.replay import run_replay
from app.runtime.runtime_engine import RuntimeEngine
from app.runtime.scheduler import Scheduler, SynchronousScheduler
from app.runtime.session_controller import (
    InvalidSessionTransitionError,
    SessionController,
    SessionState,
)
from app.runtime.shutdown import ShutdownSummary, shutdown_runtime
from app.runtime.startup import RuntimeContext, start_runtime

__all__ = [
    "EngineConfig",
    "EventProcessor",
    "HealthMonitor",
    "HealthSnapshot",
    "HistoricalReplaySource",
    "InvalidSessionTransitionError",
    "MarketDataSource",
    "ReplaySpeed",
    "RuntimeContext",
    "RuntimeEngine",
    "Scheduler",
    "SessionController",
    "SessionState",
    "ShutdownSummary",
    "StaticListSource",
    "SynchronousScheduler",
    "TradingSessionMode",
    "run_replay",
    "shutdown_runtime",
    "start_runtime",
]
