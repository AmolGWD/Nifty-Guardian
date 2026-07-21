"""
Configuration, capital state, and the single immutable output of the
Risk Engine.

RiskConfig and CapitalState are deliberately separate: RiskConfig holds
the trading-rule thresholds an operator sets once (risk per trade,
daily loss limit, ...), while CapitalState holds the account's current,
constantly-changing numbers (capital deployed, trades already taken
today, ...). CapitalState still has no defaults - it must always come
from the caller's live account state, which cannot have a sensible
static default.

Phase 15 (Parameter Injection Framework) added defaults to RiskConfig's
7 fields, sourced from app.config.defaults - the same values every
existing test helper and demo script already passed explicitly (verified
before this change: every existing construction site already supplied
all 7 fields), so this is a purely additive change with no behavior
difference for any existing caller. Range validation was added at the
same time, since RiskConfig previously had none at all.
"""

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, model_validator

from app.config.defaults import (
    DEFAULT_MAX_CAPITAL_EXPOSURE_PERCENT,
    DEFAULT_MAX_CONCURRENT_POSITIONS,
    DEFAULT_MAX_DAILY_LOSS,
    DEFAULT_MAX_TRADES_PER_DAY,
    DEFAULT_RISK_PER_TRADE_PERCENT,
    DEFAULT_STOP_LOSS_ATR_MULTIPLIER,
    DEFAULT_TARGET_ATR_MULTIPLIER,
    MAX_CAPITAL_EXPOSURE_PERCENT_RANGE,
    MAX_CONCURRENT_POSITIONS_RANGE,
    MAX_DAILY_LOSS_RANGE,
    MAX_TRADES_PER_DAY_RANGE,
    RISK_PER_TRADE_PERCENT_RANGE,
    STOP_LOSS_ATR_MULTIPLIER_RANGE,
    TARGET_ATR_MULTIPLIER_RANGE,
)
from app.config.validation import validate_range


class RiskConfig(BaseModel):
    model_config = ConfigDict(frozen=True)

    risk_per_trade_percent: float = DEFAULT_RISK_PER_TRADE_PERCENT
    stop_loss_atr_multiplier: float = DEFAULT_STOP_LOSS_ATR_MULTIPLIER
    target_atr_multiplier: float = DEFAULT_TARGET_ATR_MULTIPLIER

    max_daily_loss: float = DEFAULT_MAX_DAILY_LOSS
    max_trades_per_day: int = DEFAULT_MAX_TRADES_PER_DAY
    max_concurrent_positions: int = DEFAULT_MAX_CONCURRENT_POSITIONS
    max_capital_exposure_percent: float = DEFAULT_MAX_CAPITAL_EXPOSURE_PERCENT

    @model_validator(mode="after")
    def _validate_ranges(self) -> "RiskConfig":
        validate_range(
            "risk_per_trade_percent", self.risk_per_trade_percent, *RISK_PER_TRADE_PERCENT_RANGE
        )
        validate_range(
            "stop_loss_atr_multiplier",
            self.stop_loss_atr_multiplier,
            *STOP_LOSS_ATR_MULTIPLIER_RANGE,
        )
        validate_range(
            "target_atr_multiplier", self.target_atr_multiplier, *TARGET_ATR_MULTIPLIER_RANGE
        )
        validate_range("max_daily_loss", self.max_daily_loss, *MAX_DAILY_LOSS_RANGE)
        validate_range(
            "max_trades_per_day", self.max_trades_per_day, *MAX_TRADES_PER_DAY_RANGE
        )
        validate_range(
            "max_concurrent_positions",
            self.max_concurrent_positions,
            *MAX_CONCURRENT_POSITIONS_RANGE,
        )
        validate_range(
            "max_capital_exposure_percent",
            self.max_capital_exposure_percent,
            *MAX_CAPITAL_EXPOSURE_PERCENT_RANGE,
        )
        return self


class CapitalState(BaseModel):
    model_config = ConfigDict(frozen=True)

    total_capital: float
    capital_deployed: float
    realized_loss_today: float
    trades_taken_today: int
    open_positions: int


class RiskRejectionReason(StrEnum):
    DAILY_LOSS_LIMIT_EXCEEDED = "DailyLossLimitExceeded"
    MAX_TRADES_PER_DAY_REACHED = "MaxTradesPerDayReached"
    CAPITAL_EXPOSURE_EXCEEDED = "CapitalExposureExceeded"
    MAX_CONCURRENT_POSITIONS_REACHED = "MaxConcurrentPositionsReached"
    POSITION_SIZE_TOO_SMALL = "PositionSizeTooSmall"


class RiskAssessment(BaseModel):
    model_config = ConfigDict(frozen=True)

    risk_ok: bool

    position_size: int
    stop_loss: float
    target: float
    reward_risk_ratio: float
    capital_required: float

    rejection_reasons: list[RiskRejectionReason]
