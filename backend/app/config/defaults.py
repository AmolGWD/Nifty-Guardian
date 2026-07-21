"""
Single source of default values (and validation ranges) for every
configurable parameter in app.config.

Phase 15's backward-compatibility requirement is "existing behavior
must remain identical when every config model is constructed with no
arguments" - every DEFAULT_* value below is copied verbatim from the
hardcoded value or existing test-helper default it replaces, never
re-derived or "improved". See docs/PARAMETER_CATALOG.md for the full
per-parameter accounting (description, owning module, safe-to-optimize).
"""

# --- Strategy (app.trading.strategy.ema_breakout.EMABreakoutStrategy) ---
# Previously module-level constants (_RSI_BULLISH_THRESHOLD,
# _RSI_BEARISH_THRESHOLD, _MIN_AGREEING_CHECKS_FOR_VALID); VWAP/SuperTrend
# were previously unconditionally enabled with no toggle at all.
DEFAULT_RSI_BULLISH_THRESHOLD = 55.0
DEFAULT_RSI_BEARISH_THRESHOLD = 45.0
DEFAULT_MIN_AGREEING_CHECKS = 4
DEFAULT_VWAP_ENABLED = True
DEFAULT_SUPERTREND_ENABLED = True

RSI_THRESHOLD_RANGE = (0.0, 100.0)
MIN_AGREEING_CHECKS_RANGE = (1, 5)

# --- Risk (app.trading.risk.models.RiskConfig) ---
# Previously all 7 fields were required with no default (Phase 9's
# "nothing hardcoded" design). Values below match every existing test
# helper and demo script verbatim (tests/trading/risk/helpers.py and
# its analytics/backtest/research counterparts, scripts/demo_*.py).
DEFAULT_RISK_PER_TRADE_PERCENT = 1.0
DEFAULT_STOP_LOSS_ATR_MULTIPLIER = 1.5
DEFAULT_TARGET_ATR_MULTIPLIER = 3.0
DEFAULT_MAX_DAILY_LOSS = 5_000.0
DEFAULT_MAX_TRADES_PER_DAY = 5
DEFAULT_MAX_CONCURRENT_POSITIONS = 1
DEFAULT_MAX_CAPITAL_EXPOSURE_PERCENT = 50.0

RISK_PER_TRADE_PERCENT_RANGE = (0.1, 5.0)
STOP_LOSS_ATR_MULTIPLIER_RANGE = (0.5, 5.0)
TARGET_ATR_MULTIPLIER_RANGE = (0.5, 10.0)
MAX_DAILY_LOSS_RANGE = (0.0, 1_000_000.0)
MAX_TRADES_PER_DAY_RANGE = (1, 50)
MAX_CONCURRENT_POSITIONS_RANGE = (1, 20)
MAX_CAPITAL_EXPOSURE_PERCENT_RANGE = (1.0, 100.0)

# --- Session (app.trading.conditions - NOT wired this phase) ---
# app.trading.conditions is frozen this phase, so SessionConfig is a
# documented, unconnected placeholder (see docs/PARAMETER_CATALOG.md).
# Values mirror app.trading.conditions.engine.build_trading_conditions's
# own existing defaults, so the placeholder's "current behavior" claim
# is accurate rather than invented. "Lunch Filter" has no existing
# counterpart anywhere in the codebase - see the module docstring.
DEFAULT_OPENING_RANGE_MINUTES = 15
DEFAULT_NO_TRADE_ZONE_MINUTES = 15
DEFAULT_TRADING_START_TIME = "09:15"
DEFAULT_TRADING_END_TIME = "15:30"
DEFAULT_ALLOW_EXPIRY_DAY_TRADING = True
DEFAULT_LUNCH_FILTER_ENABLED = False
