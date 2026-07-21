# NIFTY Guardian — Parameter Catalog

Every configurable parameter introduced by Phase 15 (the Parameter
Injection Framework, `app/config/`), mirroring
`app/config/parameter_catalog.PARAMETER_CATALOG` exactly —
`tests/config/test_parameter_catalog.py` asserts every entry name below
appears in the code catalog, and vice versa, to catch drift.

This phase's objective was to **eliminate hardcoded strategy/risk
values**, not to optimize or add trading rules. Every default below
reproduces the exact behavior that existed before this phase — see each
table's "Safe To Optimize" column for which parameters are genuine
tuning levers versus safety constraints versus parameters that are
documented here but not yet connected to anything.

## Strategy parameters

Owning object: `app.config.strategy_config.StrategyParameters`, injected
into `app.trading.strategy.ema_breakout.EMABreakoutStrategy.__init__`.
`EMABreakoutStrategy()` with no arguments uses `StrategyParameters()`'s
defaults — identical to the values this module hardcoded before Phase
15.

| Name | Description | Data Type | Default | Allowed Range | Owning Module | Safe To Optimize | Reason |
|---|---|---|---|---|---|---|---|
| `rsi_bullish_threshold` | RSI value above which the RSI confirmation check reports Long | float | 55.0 | `[0.0, 100.0]`, must be > `rsi_bearish_threshold` | `app.trading.strategy.ema_breakout` | Yes | Pure signal-quality lever; no safety implication |
| `rsi_bearish_threshold` | RSI value below which the RSI confirmation check reports Short | float | 45.0 | `[0.0, 100.0]`, must be < `rsi_bullish_threshold` | `app.trading.strategy.ema_breakout` | Yes | Mirrors `rsi_bullish_threshold` for the short side |
| `vwap_enabled` | Whether the VWAP confirmation check participates in the 5-check vote | bool | `True` | `{True, False}` | `app.trading.strategy.ema_breakout` | Yes | Toggles one input signal on/off |
| `supertrend_enabled` | Whether the SuperTrend confirmation check participates in the vote | bool | `True` | `{True, False}` | `app.trading.strategy.ema_breakout` | Yes | Toggles one input signal on/off |
| `min_agreeing_checks` | Minimum agreeing checks required for a valid evaluation | int | 4 | `[1, 5]`, and `<= 3 + vwap_enabled + supertrend_enabled` | `app.trading.strategy.ema_breakout` | Yes | Controls trade frequency vs. conviction trade-off |

**On "Breakout Confirmation Candles"**: the CTO brief's example does not
have a real counterpart in this codebase — `EMABreakoutStrategy`
evaluates one `IndicatorSnapshot` at a time, not multiple candles of
confirmation. Inventing a multi-candle field would be a new trading
rule, out of this phase's scope. `min_agreeing_checks` is the closest
existing analog (it already controls how much confirmation is required)
and is documented as such above.

**On "EMA Period", "RSI Period", "ATR Multiplier", "SuperTrend
Period"**: these are not fields on `StrategyParameters` — see "Indicator
engine parameters (not yet connected)" below for why, and where they
actually live.

## Risk parameters

Owning object: `app.trading.risk.models.RiskConfig` (re-exported as
`app.config.risk_config.RiskParameters` — the same class under two
names, not a duplicate model; see that module's docstring for why).
Phase 15 added defaults (previously all 7 fields were required) and
range validation (previously none existed).

| Name | Description | Data Type | Default | Allowed Range | Owning Module | Safe To Optimize | Reason |
|---|---|---|---|---|---|---|---|
| `risk_per_trade_percent` | Percent of capital risked on a single trade; drives position sizing | float | 1.0 | `[0.1, 5.0]` | `app.trading.risk.models` | Yes | Core risk/reward sizing lever |
| `stop_loss_atr_multiplier` | ATR multiple used to place the stop loss | float | 1.5 | `[0.5, 5.0]` | `app.trading.risk.models` | Yes | Signal-quality/reward-risk lever |
| `target_atr_multiplier` | ATR multiple used to place the target | float | 3.0 | `[0.5, 10.0]` | `app.trading.risk.models` | Yes | Signal-quality/reward-risk lever |
| `max_daily_loss` | Daily realized-loss circuit breaker | float | 5000.0 | `[0.0, 1000000.0]` | `app.trading.risk.models` | No | Capital-protection circuit breaker — optimizing it to raise backtest returns defeats its purpose |
| `max_trades_per_day` | Maximum trades permitted in a single trading day | int | 5 | `[1, 50]` | `app.trading.risk.models` | No | Operational safety cap, not a signal parameter |
| `max_concurrent_positions` | Maximum open positions permitted at once | int | 1 | `[1, 20]` | `app.trading.risk.models` | No | Capital-safety constraint |
| `max_capital_exposure_percent` | Maximum percent of total capital allowed deployed at once | float | 50.0 | `[1.0, 100.0]` | `app.trading.risk.models` | No | Capital-safety constraint |

**On "Reward/Risk Ratio"**: not a separate input field — it's
`RiskAssessment.reward_risk_ratio`, an *output* of the Risk Engine
derived from `target_atr_multiplier` / `stop_loss_atr_multiplier`.

## Session parameters — not wired this phase

Owning object: `app.config.session_config.SessionParameters`. Every
field below maps onto `app.trading.conditions`, which is **explicitly
frozen this phase** ("Modify ONLY the strategy and risk modules where
necessary" — CTO brief). This model exists so these parameters are
documented and validated with the shape they'll need later, without
inventing a fake connection today — the same "unconnected placeholder"
pattern as Phase 14's `Experiment.parameters` (see
`docs/RESEARCH_GUIDE.md`, "Parameter management").

| Name | Description | Data Type | Default | Allowed Range | Owning Module | Safe To Optimize | Reason |
|---|---|---|---|---|---|---|---|
| `opening_range_minutes` | Minutes after market open during which entries are blocked | int | 15 | `[0, 120]` (not enforced on `app.trading.conditions` this phase) | `app.trading.conditions` (frozen) | N/A | Not wired this phase |
| `no_trade_zone_minutes` | Minutes before market close during which entries are blocked | int | 15 | `[0, 120]` (not enforced this phase) | `app.trading.conditions` (frozen) | N/A | Not wired this phase |
| `trading_start_time` | Trading session start time (HH:MM) | str | `"09:15"` | valid HH:MM, must be before `trading_end_time` | `app.core.config` (frozen) | N/A | Mirrors `Settings.market_open`; not wired this phase |
| `trading_end_time` | Trading session end time (HH:MM) | str | `"15:30"` | valid HH:MM, must be after `trading_start_time` | `app.core.config` (frozen) | N/A | Mirrors `Settings.market_close`; not wired this phase |
| `allow_expiry_day_trading` | Whether trading is permitted on an option's own expiry day | bool | `True` | `{True, False}` (not enforced this phase) | `app.trading.conditions` (frozen) | N/A | Not wired this phase |
| `lunch_filter_enabled` | Placeholder for a midday/lunch-break no-trade filter | bool | `False` | `{True, False}` — inert | none exists | N/A | Named in the CTO brief's examples, but no such filter has ever been implemented anywhere in this codebase; kept as an honest, documented placeholder rather than a new trading rule |

## Indicator engine parameters — not yet connected

The CTO brief lists EMA Period, RSI Period, ATR Multiplier, and
SuperTrend Period among its `StrategyConfig` examples. They are **not**
fields on `StrategyParameters`: `EMABreakoutStrategy` never computes
indicators itself, it consumes a pre-built `IndicatorSnapshot` — these
periods belong one layer below, to
`app.trading.indicators.engine.calculate_indicator_snapshot`, which has
already accepted them as keyword parameters (with the same defaults
below) since Phase 5. Their only current callers —
`app.trading.backtest.backtest_engine` and
`app.trading.analytics.regime_analysis` — are both frozen this phase, so
wiring them through `app.config` would require touching frozen code and
was left for a future phase.

| Name | Description | Data Type | Default | Owning Module |
|---|---|---|---|---|
| `ema_period` | Candle period used to compute the EMA indicator value | int | 20 | `app.trading.indicators.engine.calculate_indicator_snapshot` |
| `rsi_period` | Candle period used to compute the RSI indicator value | int | 14 | `app.trading.indicators.engine.calculate_indicator_snapshot` |
| `supertrend_period` | Candle period used to compute the SuperTrend indicator | int | 10 | `app.trading.indicators.engine.calculate_indicator_snapshot` |
| `supertrend_multiplier` | ATR multiplier used to compute the SuperTrend indicator's bands | float | 3.0 | `app.trading.indicators.engine.calculate_indicator_snapshot` |
| `atr_period` | Candle period used to compute ATR/ATR percent | int | 14 | `app.trading.indicators.engine.calculate_indicator_snapshot` |

## Backward compatibility

Every default above is copied verbatim from the value it replaces (a
hardcoded module constant, or a value every existing test
helper/demo script already passed explicitly) — see
`app/config/defaults.py`'s module docstring and comments for the exact
provenance of each one. `tests/config/`, plus the extended
`tests/trading/strategy/test_ema_breakout.py` and the new
`tests/trading/risk/test_models.py`, prove that constructing every
config model with no arguments reproduces the exact pre-Phase-15
behavior; the full 375-test suite that existed before this phase passes
completely unchanged.
