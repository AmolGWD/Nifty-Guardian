"""
Configuration, capital state, and the single immutable output of the
Risk Engine.

RiskConfig and CapitalState are deliberately separate: RiskConfig holds
the trading-rule thresholds an operator sets once (risk per trade,
daily loss limit, ...), while CapitalState holds the account's current,
constantly-changing numbers (capital deployed, trades already taken
today, ...). Neither has defaults - both must come from the caller
(ultimately `app.core.config`), consistent with "nothing hardcoded".
"""

from enum import StrEnum

from pydantic import BaseModel, ConfigDict


class RiskConfig(BaseModel):
    model_config = ConfigDict(frozen=True)

    risk_per_trade_percent: float
    stop_loss_atr_multiplier: float
    target_atr_multiplier: float

    max_daily_loss: float
    max_trades_per_day: int
    max_concurrent_positions: int
    max_capital_exposure_percent: float


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
