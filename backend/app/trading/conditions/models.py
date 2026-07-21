"""
The single, immutable output of the Trading Conditions layer.

gap_filter_ok and position_guard_ok are included alongside the named
example fields from the brief (session_valid, opening_range_complete,
within_trading_window, expiry_allowed, liquidity_ok, cooldown_complete)
since the brief's field list was explicitly given as examples, not an
exhaustive spec - every evaluator's result should be visible here, not
silently folded away.
"""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict


class NoTradeReason(StrEnum):
    SESSION_INVALID = "SessionInvalid"
    OUTSIDE_TRADING_WINDOW = "OutsideTradingWindow"
    WITHIN_OPENING_RANGE = "WithinOpeningRange"
    EXPIRY_NOT_ALLOWED = "ExpiryNotAllowed"
    POSITION_ALREADY_OPEN = "PositionAlreadyOpen"
    COOLDOWN_ACTIVE = "CooldownActive"
    GAP_TOO_LARGE = "GapTooLarge"
    INSUFFICIENT_LIQUIDITY = "InsufficientLiquidity"


class TradingConditions(BaseModel):
    model_config = ConfigDict(frozen=True)

    as_of: datetime

    can_trade: bool
    no_trade_reason: NoTradeReason | None

    session_valid: bool
    opening_range_complete: bool
    within_trading_window: bool
    expiry_allowed: bool
    liquidity_ok: bool
    cooldown_complete: bool
    gap_filter_ok: bool
    position_guard_ok: bool
