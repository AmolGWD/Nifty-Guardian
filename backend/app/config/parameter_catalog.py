"""
Programmatic parameter catalog - one ParameterDescriptor per
configurable parameter, mirrored by hand in docs/PARAMETER_CATALOG.md.

tests/config/test_parameter_catalog.py asserts every entry's name
appears in the markdown file, to catch drift between the two without a
full auto-generation pipeline (a pipeline would be more machinery than
this phase's scope justifies).

Includes entries for parameters that are NOT wired into anything this
phase (SessionParameters' fields, and the indicator-engine periods that
StrategyParameters deliberately excludes - see strategy_config.py's
docstring) so the catalog is a complete, honest accounting of every
parameter the CTO brief named, not just the ones this phase connected.
"""

from pydantic import BaseModel, ConfigDict


class ParameterDescriptor(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str
    description: str
    data_type: str
    default_value: str
    allowed_range: str
    owning_module: str
    safe_to_optimize: str
    reason: str


PARAMETER_CATALOG: tuple[ParameterDescriptor, ...] = (
    # --- Strategy: app.config.strategy_config.StrategyParameters,
    # injected into app.trading.strategy.ema_breakout.EMABreakoutStrategy ---
    ParameterDescriptor(
        name="rsi_bullish_threshold",
        description="RSI value above which the RSI confirmation check reports Long.",
        data_type="float",
        default_value="55.0",
        allowed_range="[0.0, 100.0], must be > rsi_bearish_threshold",
        owning_module="app.trading.strategy.ema_breakout",
        safe_to_optimize="Yes",
        reason="Pure signal-quality lever; changing it never bypasses a risk or safety control.",
    ),
    ParameterDescriptor(
        name="rsi_bearish_threshold",
        description="RSI value below which the RSI confirmation check reports Short.",
        data_type="float",
        default_value="45.0",
        allowed_range="[0.0, 100.0], must be < rsi_bullish_threshold",
        owning_module="app.trading.strategy.ema_breakout",
        safe_to_optimize="Yes",
        reason="Same as rsi_bullish_threshold, mirrored for the short side.",
    ),
    ParameterDescriptor(
        name="vwap_enabled",
        description="Whether the VWAP confirmation check participates in the 5-check vote.",
        data_type="bool",
        default_value="True",
        allowed_range="{True, False}",
        owning_module="app.trading.strategy.ema_breakout",
        safe_to_optimize="Yes",
        reason="Toggles one input signal on/off; no safety implication.",
    ),
    ParameterDescriptor(
        name="supertrend_enabled",
        description="Whether the SuperTrend confirmation check participates in the vote.",
        data_type="bool",
        default_value="True",
        allowed_range="{True, False}",
        owning_module="app.trading.strategy.ema_breakout",
        safe_to_optimize="Yes",
        reason="Toggles one input signal on/off; no safety implication.",
    ),
    ParameterDescriptor(
        name="min_agreeing_checks",
        description=(
            "Minimum number of agreeing checks required for a strategy evaluation to be "
            "valid. Closest existing analog to the brief's 'Breakout Confirmation Candles' - "
            "this codebase evaluates one snapshot at a time, not multiple candles of "
            "confirmation, so a multi-candle field was not invented (would be a new trading "
            "rule, out of this phase's scope)."
        ),
        data_type="int",
        default_value="4",
        allowed_range="[1, 5], and <= 3 + vwap_enabled + supertrend_enabled",
        owning_module="app.trading.strategy.ema_breakout",
        safe_to_optimize="Yes",
        reason="Controls trade frequency vs. conviction trade-off; a signal-quality lever.",
    ),
    # --- Risk: app.trading.risk.models.RiskConfig, re-exported as
    # app.config.risk_config.RiskParameters ---
    ParameterDescriptor(
        name="risk_per_trade_percent",
        description="Percent of capital risked on a single trade; drives position sizing.",
        data_type="float",
        default_value="1.0",
        allowed_range="[0.1, 5.0]",
        owning_module="app.trading.risk.models",
        safe_to_optimize="Yes",
        reason="Core risk/reward sizing lever.",
    ),
    ParameterDescriptor(
        name="stop_loss_atr_multiplier",
        description="ATR multiple used to place the stop loss.",
        data_type="float",
        default_value="1.5",
        allowed_range="[0.5, 5.0]",
        owning_module="app.trading.risk.models",
        safe_to_optimize="Yes",
        reason="Signal-quality/reward-risk lever, not a safety cap.",
    ),
    ParameterDescriptor(
        name="target_atr_multiplier",
        description=(
            "ATR multiple used to place the target. Reward/Risk Ratio (a brief example) is "
            "derived from this divided by stop_loss_atr_multiplier - it is a RiskAssessment "
            "output field, not a separate input parameter."
        ),
        data_type="float",
        default_value="3.0",
        allowed_range="[0.5, 10.0]",
        owning_module="app.trading.risk.models",
        safe_to_optimize="Yes",
        reason="Signal-quality/reward-risk lever, not a safety cap.",
    ),
    ParameterDescriptor(
        name="max_daily_loss",
        description="Daily realized-loss circuit breaker; new trades are rejected past it.",
        data_type="float",
        default_value="5000.0",
        allowed_range="[0.0, 1000000.0]",
        owning_module="app.trading.risk.models",
        safe_to_optimize="No",
        reason="Capital-protection circuit breaker - optimizing it to raise backtest returns "
        "defeats its purpose as a safety limit.",
    ),
    ParameterDescriptor(
        name="max_trades_per_day",
        description="Maximum number of trades permitted in a single trading day.",
        data_type="int",
        default_value="5",
        allowed_range="[1, 50]",
        owning_module="app.trading.risk.models",
        safe_to_optimize="No",
        reason="Operational safety cap, not a signal parameter to curve-fit.",
    ),
    ParameterDescriptor(
        name="max_concurrent_positions",
        description="Maximum number of open positions permitted at once.",
        data_type="int",
        default_value="1",
        allowed_range="[1, 20]",
        owning_module="app.trading.risk.models",
        safe_to_optimize="No",
        reason="Capital-safety constraint, not a signal parameter.",
    ),
    ParameterDescriptor(
        name="max_capital_exposure_percent",
        description="Maximum percent of total capital allowed deployed at once.",
        data_type="float",
        default_value="50.0",
        allowed_range="[1.0, 100.0]",
        owning_module="app.trading.risk.models",
        safe_to_optimize="No",
        reason="Capital-safety constraint, not a signal parameter.",
    ),
    # --- Session: app.config.session_config.SessionParameters - NOT
    # wired this phase; app.trading.conditions is frozen. ---
    ParameterDescriptor(
        name="opening_range_minutes",
        description="Minutes after market open during which entries are blocked.",
        data_type="int",
        default_value="15",
        allowed_range="[0, 120] (not enforced on app.trading.conditions this phase)",
        owning_module="app.trading.conditions (frozen; not connected via app.config)",
        safe_to_optimize="N/A",
        reason="Not wired this phase - app.trading.conditions is frozen; documented for "
        "completeness only.",
    ),
    ParameterDescriptor(
        name="no_trade_zone_minutes",
        description="Minutes before market close during which entries are blocked.",
        data_type="int",
        default_value="15",
        allowed_range="[0, 120] (not enforced on app.trading.conditions this phase)",
        owning_module="app.trading.conditions (frozen; not connected via app.config)",
        safe_to_optimize="N/A",
        reason="Not wired this phase - app.trading.conditions is frozen.",
    ),
    ParameterDescriptor(
        name="trading_start_time",
        description="Trading session start time (HH:MM).",
        data_type="str",
        default_value="09:15",
        allowed_range="valid HH:MM, must be before trading_end_time (not enforced this phase)",
        owning_module="app.core.config (frozen; not connected via app.config)",
        safe_to_optimize="N/A",
        reason="Not wired this phase - mirrors app.core.config.Settings.market_open.",
    ),
    ParameterDescriptor(
        name="trading_end_time",
        description="Trading session end time (HH:MM).",
        data_type="str",
        default_value="15:30",
        allowed_range="valid HH:MM, must be after trading_start_time (not enforced this phase)",
        owning_module="app.core.config (frozen; not connected via app.config)",
        safe_to_optimize="N/A",
        reason="Not wired this phase - mirrors app.core.config.Settings.market_close.",
    ),
    ParameterDescriptor(
        name="allow_expiry_day_trading",
        description="Whether trading is permitted on an option's own expiry day.",
        data_type="bool",
        default_value="True",
        allowed_range="{True, False} (not enforced on app.trading.conditions this phase)",
        owning_module="app.trading.conditions (frozen; not connected via app.config)",
        safe_to_optimize="N/A",
        reason="Not wired this phase - app.trading.conditions is frozen.",
    ),
    ParameterDescriptor(
        name="lunch_filter_enabled",
        description="Placeholder for a midday/lunch-break no-trade filter.",
        data_type="bool",
        default_value="False",
        allowed_range="{True, False} - inert, no implementation exists",
        owning_module="none - no lunch filter exists anywhere in this codebase",
        safe_to_optimize="N/A",
        reason="Named in the CTO brief's SessionConfig examples, but no such filter has ever "
        "been implemented in app.trading.conditions; kept as an honest, documented "
        "placeholder rather than inventing a new trading rule.",
    ),
    # --- Indicator-engine periods: brief's StrategyConfig examples that
    # live one layer below the strategy, already parameterized since
    # Phase 5 - NOT re-exposed via app.config this phase. ---
    ParameterDescriptor(
        name="ema_period",
        description="Candle period used to compute the EMA indicator value.",
        data_type="int",
        default_value="20",
        allowed_range="positive int (validated by app.trading.indicators.ema, not app.config)",
        owning_module="app.trading.indicators.engine.calculate_indicator_snapshot",
        safe_to_optimize="N/A",
        reason="Already a keyword parameter (with this default) since Phase 5, but its only "
        "callers - app.trading.backtest/app.trading.analytics - are frozen this phase, so "
        "it is not reachable through app.config yet.",
    ),
    ParameterDescriptor(
        name="rsi_period",
        description="Candle period used to compute the RSI indicator value.",
        data_type="int",
        default_value="14",
        allowed_range="positive int (validated by app.trading.indicators.rsi, not app.config)",
        owning_module="app.trading.indicators.engine.calculate_indicator_snapshot",
        safe_to_optimize="N/A",
        reason="Same as ema_period - parameterized at the indicator engine since Phase 5, not "
        "reachable through app.config yet.",
    ),
    ParameterDescriptor(
        name="supertrend_period",
        description="Candle period used to compute the SuperTrend indicator.",
        data_type="int",
        default_value="10",
        allowed_range="positive int (validated by app.trading.indicators.supertrend)",
        owning_module="app.trading.indicators.engine.calculate_indicator_snapshot",
        safe_to_optimize="N/A",
        reason="Same as ema_period - not reachable through app.config yet.",
    ),
    ParameterDescriptor(
        name="supertrend_multiplier",
        description="ATR multiplier used to compute the SuperTrend indicator's bands.",
        data_type="float",
        default_value="3.0",
        allowed_range="positive float (validated by app.trading.indicators.supertrend)",
        owning_module="app.trading.indicators.engine.calculate_indicator_snapshot",
        safe_to_optimize="N/A",
        reason="Same as ema_period - not reachable through app.config yet.",
    ),
    ParameterDescriptor(
        name="atr_period",
        description="Candle period used to compute ATR/ATR percent.",
        data_type="int",
        default_value="14",
        allowed_range="positive int (validated by app.trading.indicators.volatility)",
        owning_module="app.trading.indicators.engine.calculate_indicator_snapshot",
        safe_to_optimize="N/A",
        reason="Same as ema_period - not reachable through app.config yet.",
    ),
)
