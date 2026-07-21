"""
StrategyParameters - the configurable inputs to
app.trading.strategy.ema_breakout.EMABreakoutStrategy.

Defaults are copied verbatim from the values EMABreakoutStrategy
hardcoded before Phase 15 - constructing this with no arguments and
injecting it into EMABreakoutStrategy() must reproduce identical
behavior (see docs/PARAMETER_CATALOG.md's backward-compatibility note
and tests/config/test_strategy_config.py).

Several parameters the CTO brief names as StrategyConfig examples (EMA
Period, RSI Period, ATR Multiplier, SuperTrend Period) are deliberately
NOT fields here: EMABreakoutStrategy never computes indicators itself -
it consumes a pre-built IndicatorSnapshot - so those periods belong to
app.trading.indicators.engine.calculate_indicator_snapshot instead,
which has been parameterized (with matching defaults) since Phase 5.
Wiring them through app.config would require changing call sites in
app.trading.backtest and app.trading.analytics, both frozen this phase.
See docs/PARAMETER_CATALOG.md for the full accounting of what is (and
isn't) connected this phase.
"""

from pydantic import BaseModel, ConfigDict, model_validator

from app.config.defaults import (
    DEFAULT_MIN_AGREEING_CHECKS,
    DEFAULT_RSI_BEARISH_THRESHOLD,
    DEFAULT_RSI_BULLISH_THRESHOLD,
    DEFAULT_SUPERTREND_ENABLED,
    DEFAULT_VWAP_ENABLED,
    MIN_AGREEING_CHECKS_RANGE,
    RSI_THRESHOLD_RANGE,
)
from app.config.validation import ParameterValidationError, validate_less_than, validate_range


class StrategyParameters(BaseModel):
    model_config = ConfigDict(frozen=True)

    rsi_bullish_threshold: float = DEFAULT_RSI_BULLISH_THRESHOLD
    rsi_bearish_threshold: float = DEFAULT_RSI_BEARISH_THRESHOLD
    vwap_enabled: bool = DEFAULT_VWAP_ENABLED
    supertrend_enabled: bool = DEFAULT_SUPERTREND_ENABLED
    min_agreeing_checks: int = DEFAULT_MIN_AGREEING_CHECKS

    @model_validator(mode="after")
    def _validate(self) -> "StrategyParameters":
        validate_range("rsi_bullish_threshold", self.rsi_bullish_threshold, *RSI_THRESHOLD_RANGE)
        validate_range("rsi_bearish_threshold", self.rsi_bearish_threshold, *RSI_THRESHOLD_RANGE)
        validate_less_than(
            "rsi_bearish_threshold",
            self.rsi_bearish_threshold,
            "rsi_bullish_threshold",
            self.rsi_bullish_threshold,
        )
        validate_range(
            "min_agreeing_checks", self.min_agreeing_checks, *MIN_AGREEING_CHECKS_RANGE
        )

        max_possible_checks = 3 + int(self.vwap_enabled) + int(self.supertrend_enabled)
        if self.min_agreeing_checks > max_possible_checks:
            raise ParameterValidationError(
                f"min_agreeing_checks={self.min_agreeing_checks} can never be satisfied: "
                f"only {max_possible_checks} checks are enabled "
                f"(vwap_enabled={self.vwap_enabled}, supertrend_enabled={self.supertrend_enabled})"
            )
        return self
