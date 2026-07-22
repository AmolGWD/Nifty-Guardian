"""
Signal Engine: turns already-decided, already-filled paper trades
(frozen `app.paper_trading`/`app.runtime`/`app.live`) into a
human-reportable signal - a Guardian Score, dashboard state, a
Telegram alert, a dummy trade record, and daily performance reporting.
No new trading, broker, or runtime logic lives here.
"""

from app.signals.confidence_engine import compute_guardian_score, compute_reward_risk_ratio
from app.signals.dummy_trade_tracker import DummyTradeTracker
from app.signals.models import (
    DailyPerformanceReport,
    DummyTrade,
    DummyTradeStatus,
    ExitReason,
    GuardianScore,
    SignalConfig,
    SignalType,
)
from app.signals.signal_filter import FilterDecision, SignalFilter
from app.signals.signal_runtime import SignalEngineContext, start_signal_engine
from app.signals.signal_service import CurrentSignalState, SignalService

__all__ = [
    "CurrentSignalState",
    "DailyPerformanceReport",
    "DummyTrade",
    "DummyTradeStatus",
    "DummyTradeTracker",
    "ExitReason",
    "FilterDecision",
    "GuardianScore",
    "SignalConfig",
    "SignalEngineContext",
    "SignalFilter",
    "SignalService",
    "SignalType",
    "compute_guardian_score",
    "compute_reward_risk_ratio",
    "start_signal_engine",
]
