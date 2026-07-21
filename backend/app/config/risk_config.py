"""
RiskParameters - app.config's public name for the Risk Engine's config
object.

There is no separate RiskParameters model with its own 7 duplicated
fields: app.trading.risk.models.RiskConfig is already the immutable,
Pydantic configuration object the CTO brief asks for (Phase 9) - it
just had no defaults and no validation before Phase 15. Both were added
directly to RiskConfig itself (sourced from app.config.defaults, the
same constants this module re-exports for documentation purposes),
because RiskConfig is the single object every risk-engine function
already takes; a second, parallel "RiskParameters" model with the same
fields would be two things to keep in sync for no behavioral benefit.

This module is named risk_config.py (per the brief's suggested
structure) and re-exports the class as RiskParameters, not RiskConfig,
purely so `from app.config import RiskParameters` cannot be confused
with `from app.trading.risk.models import RiskConfig` at an import
site - they are the same class under two names.
"""

from app.config.defaults import (
    MAX_CAPITAL_EXPOSURE_PERCENT_RANGE,
    MAX_CONCURRENT_POSITIONS_RANGE,
    MAX_DAILY_LOSS_RANGE,
    MAX_TRADES_PER_DAY_RANGE,
    RISK_PER_TRADE_PERCENT_RANGE,
    STOP_LOSS_ATR_MULTIPLIER_RANGE,
    TARGET_ATR_MULTIPLIER_RANGE,
)
from app.trading.risk.models import RiskConfig as RiskParameters

__all__ = [
    "RiskParameters",
    "RISK_PER_TRADE_PERCENT_RANGE",
    "STOP_LOSS_ATR_MULTIPLIER_RANGE",
    "TARGET_ATR_MULTIPLIER_RANGE",
    "MAX_DAILY_LOSS_RANGE",
    "MAX_TRADES_PER_DAY_RANGE",
    "MAX_CONCURRENT_POSITIONS_RANGE",
    "MAX_CAPITAL_EXPOSURE_PERCENT_RANGE",
]
