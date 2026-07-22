"""
Core types for the Signal Engine: the Guardian Score (this package's
own, new, numeric confidence aggregate - distinct from
`app.trading.strategy.models.StrategyStrength`, which stays exactly
what it always was, a coarse categorical read), dummy (paper) trades,
and daily performance reporting.

Nothing here duplicates `app.trading`/`app.paper_trading` - every
field either reuses a frozen type directly (`StrategyDirection`) or
holds a new concept those packages never modeled (a numeric score, a
paper-trade record enriched with R-multiple/duration/exit-reason).
"""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.trading.strategy.models import StrategyDirection, StrategyStrength


class SignalType(StrEnum):
    BUY_CE = "BuyCE"
    BUY_PE = "BuyPE"
    TARGET_HIT = "TargetHit"
    STOPLOSS_HIT = "StoplossHit"
    NO_TRADE = "NoTrade"


class ExitReason(StrEnum):
    TARGET = "Target"
    STOP_LOSS = "StopLoss"
    END_OF_DAY = "EndOfDay"
    UNKNOWN = "Unknown"


class DummyTradeStatus(StrEnum):
    OPEN = "Open"
    CLOSED = "Closed"


class GuardianScore(BaseModel):
    """
    A single, explainable 0-100 number blending the Strategy Engine's
    categorical `strength` with the Risk Engine's reward:risk quality -
    see `confidence_engine.py` for the exact, documented formula. Never
    a replacement for `strength` - both are reported side by side (the
    brief's "Confidence" field is `strength`; "Guardian Score" is this).
    """

    model_config = ConfigDict(frozen=True)

    score: float
    strength: StrategyStrength
    reward_risk_ratio: float
    reasons: list[str]

    @model_validator(mode="after")
    def _validate(self) -> "GuardianScore":
        if not (0.0 <= self.score <= 100.0):
            raise ValueError("score must be between 0 and 100")
        return self


class DummyTrade(BaseModel):
    """
    A paper trade this engine creates for every accepted signal - never
    a real order, never sent to any broker. Entry/SL/target come
    straight from the already-filled `app.paper_trading.models.Order`
    (Phase 19, frozen) that triggered it; exit fields are filled in
    once the underlying `Position` (also frozen) closes.
    """

    trade_id: str
    strategy_name: str
    direction: StrategyDirection
    guardian_score: GuardianScore

    entry_price: float
    stop_loss: float
    target: float
    quantity: int

    opened_at: datetime
    status: DummyTradeStatus = DummyTradeStatus.OPEN

    exit_price: float | None = None
    closed_at: datetime | None = None
    pnl: float | None = None
    r_multiple: float | None = None
    duration_seconds: float | None = None
    exit_reason: ExitReason | None = None

    def close(
        self, *, exit_price: float, closed_at: datetime, pnl: float, exit_reason: ExitReason
    ) -> "DummyTrade":
        risk_per_unit = abs(self.entry_price - self.stop_loss)
        pnl_per_unit = pnl / self.quantity if self.quantity else 0.0
        r_multiple = (pnl_per_unit / risk_per_unit) if risk_per_unit > 0 else 0.0
        return self.model_copy(
            update={
                "status": DummyTradeStatus.CLOSED,
                "exit_price": exit_price,
                "closed_at": closed_at,
                "pnl": pnl,
                "r_multiple": round(r_multiple, 4),
                "duration_seconds": (closed_at - self.opened_at).total_seconds(),
                "exit_reason": exit_reason,
            }
        )


class DailyPerformanceReport(BaseModel):
    model_config = ConfigDict(frozen=True)

    report_date: str  # ISO date (YYYY-MM-DD) - keeps the JSON export human-readable
    total_signals: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    net_points: float
    average_reward_risk_ratio: float
    best_trade: DummyTrade | None
    worst_trade: DummyTrade | None


class SignalConfig(BaseSettings):
    """
    Every "configurable" knob the brief names for signal filtering -
    environment-driven, never hardcoded, same convention as
    `app.live.models.LiveConfig` (Phase 24).
    """

    model_config = SettingsConfigDict(
        env_prefix="SIGNAL_", env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    confidence_threshold: float = 65.0
    cooldown_minutes: float = 15.0
    max_signals_per_day: int = 5

    @model_validator(mode="after")
    def _validate(self) -> "SignalConfig":
        if not (0.0 <= self.confidence_threshold <= 100.0):
            raise ValueError("SIGNAL_CONFIDENCE_THRESHOLD must be between 0 and 100")
        if self.cooldown_minutes < 0:
            raise ValueError("SIGNAL_COOLDOWN_MINUTES must not be negative")
        if self.max_signals_per_day <= 0:
            raise ValueError("SIGNAL_MAX_SIGNALS_PER_DAY must be positive")
        return self
