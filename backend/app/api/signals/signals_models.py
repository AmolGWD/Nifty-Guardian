"""
REST response models for the Signal Engine API - a new, additive
surface parallel to `app.api.dashboard` (Phase 22, frozen), never
modifying it. Every field reuses `app.signals`' own frozen-shaped
types directly rather than duplicating them.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.notifications.models import TelegramStatus
from app.signals.models import DummyTradeStatus, ExitReason, SignalType
from app.signals.signal_filter import SessionPhase
from app.trading.strategy.models import StrategyDirection, StrategyStrength


class GuardianScoreResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    score: float
    strength: StrategyStrength
    reward_risk_ratio: float
    reasons: list[str]


class DummyTradeResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    trade_id: str
    strategy_name: str
    direction: StrategyDirection
    guardian_score: GuardianScoreResponse
    entry_price: float
    stop_loss: float
    target: float
    quantity: int
    opened_at: datetime
    status: DummyTradeStatus
    exit_price: float | None
    closed_at: datetime | None
    pnl: float | None
    r_multiple: float | None
    duration_seconds: float | None
    exit_reason: ExitReason | None


class SignalStateResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    market_status: SessionPhase | None
    market_bias: StrategyDirection
    latest_signal_type: SignalType | None
    latest_guardian_score: GuardianScoreResponse | None
    latest_explanation: str | None
    latest_signal_at: datetime | None
    latest_entry_price: float | None
    latest_stop_loss: float | None
    latest_target: float | None
    signals_sent_today: int
    telegram_status: TelegramStatus | None


class PerformanceResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    open_trades: list[DummyTradeResponse]
    closed_trades: list[DummyTradeResponse]
    win_rate: float
    today_pnl: float
    weekly_pnl: float
    monthly_pnl: float


class DailyReportResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    report_date: str
    total_signals: int
    buy_ce_count: int
    buy_pe_count: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    net_points: float
    average_pnl: float
    average_reward_risk_ratio: float
    best_trade: DummyTradeResponse | None
    worst_trade: DummyTradeResponse | None
    highest_guardian_score: float
    average_hold_time_seconds: float
    market_bias: StrategyDirection
    guardian_status: str


class EngineStatusResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    running: bool
    live_session_state: str | None


class ExportReportResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    path: str
