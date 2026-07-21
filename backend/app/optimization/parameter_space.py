"""
ParameterSpace: the set of parameters one grid search run sweeps, each
with a Name/Description/Type/Minimum/Maximum/Step/Default/Safe To
Optimize, per the CTO brief's PARAMETER SPACE section.

`_EXCLUDED_FROM_OPTIMIZATION` is an enforced guardrail, not just a
comment: the brief's "Do NOT optimize" list (session filters, VWAP
toggle, SuperTrend toggle, expiry filters) can never be added to a
`ParameterSpace` - `ParameterSpace` raises `ParameterValidationError`
if asked to, rather than relying on every caller remembering not to.
These parameters are also a poor fit for this model's
minimum/maximum/step shape (they're booleans/session windows, not
swept numeric ranges), so excluding them structurally is a better fit
than trying to force them into a grid dimension.

DEFAULT_PARAMETER_CATALOG covers exactly the six parameters the CTO
brief names ("INITIAL PARAMETERS"). Not every one of them can currently
change a real backtest outcome - see `docs/OPTIMIZATION_GUIDE.md` and
`executor.py`'s module docstring for the full accounting of which are
genuinely wired (via Phase 16's narrow, CTO-authorized exception to
`app.trading.backtest`) versus not.
"""

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, model_validator

from app.config.validation import ParameterValidationError

_EXCLUDED_FROM_OPTIMIZATION: frozenset[str] = frozenset(
    {
        "vwap_enabled",
        "supertrend_enabled",
        "opening_range_minutes",
        "no_trade_zone_minutes",
        "trading_start_time",
        "trading_end_time",
        "lunch_filter_enabled",
        "allow_expiry_day_trading",
    }
)


class ParameterType(StrEnum):
    INT = "int"
    FLOAT = "float"


class OptimizableParameter(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str
    description: str
    parameter_type: ParameterType
    minimum: float
    maximum: float
    step: float
    default: float
    safe_to_optimize: bool

    @model_validator(mode="after")
    def _validate(self) -> "OptimizableParameter":
        if self.name in _EXCLUDED_FROM_OPTIMIZATION:
            raise ParameterValidationError(
                f"{self.name!r} is on the CTO brief's 'Do NOT optimize' list and cannot be "
                "included in a search space"
            )
        if self.step <= 0:
            raise ParameterValidationError(f"step={self.step} must be positive")
        if self.minimum >= self.maximum:
            raise ParameterValidationError(
                f"minimum={self.minimum} must be less than maximum={self.maximum}"
            )
        if not (self.minimum <= self.default <= self.maximum):
            raise ParameterValidationError(
                f"default={self.default} is outside [{self.minimum}, {self.maximum}]"
            )
        return self

    def values(self) -> tuple[int, ...] | tuple[float, ...]:
        """Deterministic grid values from minimum to maximum inclusive, in step increments."""
        steps = round((self.maximum - self.minimum) / self.step)
        raw_values = [self.minimum + i * self.step for i in range(steps + 1)]

        if self.parameter_type is ParameterType.INT:
            return tuple(int(round(value)) for value in raw_values)
        return tuple(round(value, 10) for value in raw_values)


class ParameterSpace(BaseModel):
    model_config = ConfigDict(frozen=True)

    parameters: tuple[OptimizableParameter, ...]

    @model_validator(mode="after")
    def _validate(self) -> "ParameterSpace":
        if not self.parameters:
            raise ParameterValidationError("ParameterSpace must contain at least one parameter")

        names = [parameter.name for parameter in self.parameters]
        if len(names) != len(set(names)):
            raise ParameterValidationError(f"duplicate parameter names in ParameterSpace: {names}")
        return self

    def dimension_names(self) -> tuple[str, ...]:
        return tuple(parameter.name for parameter in self.parameters)

    def total_combinations(self) -> int:
        total = 1
        for parameter in self.parameters:
            total *= len(parameter.values())
        return total


EMA_PERIOD = OptimizableParameter(
    name="ema_period",
    description="Candle period used to compute the EMA indicator value.",
    parameter_type=ParameterType.INT,
    minimum=10,
    maximum=30,
    step=2,
    default=20,
    safe_to_optimize=True,
)

RSI_BULLISH_THRESHOLD = OptimizableParameter(
    name="rsi_bullish_threshold",
    description="RSI value above which the RSI confirmation check reports Long.",
    parameter_type=ParameterType.FLOAT,
    minimum=50,
    maximum=60,
    step=5,
    default=55.0,
    safe_to_optimize=True,
)

RSI_BEARISH_THRESHOLD = OptimizableParameter(
    name="rsi_bearish_threshold",
    description="RSI value below which the RSI confirmation check reports Short.",
    parameter_type=ParameterType.FLOAT,
    minimum=35,
    maximum=45,
    step=5,
    default=45.0,
    safe_to_optimize=True,
)

REWARD_RISK_RATIO = OptimizableParameter(
    name="reward_risk_ratio",
    description=(
        "Target distance / stop-loss distance. Not a direct RiskConfig field - applied by "
        "setting target_atr_multiplier = reward_risk_ratio * stop_loss_atr_multiplier, holding "
        "stop_loss_atr_multiplier fixed at the base configuration's value (see executor.py)."
    ),
    parameter_type=ParameterType.FLOAT,
    minimum=1.5,
    maximum=2.5,
    step=0.5,
    default=2.0,
    safe_to_optimize=True,
)

RISK_PERCENT = OptimizableParameter(
    name="risk_percent",
    description="Percent of capital risked per trade (RiskConfig.risk_per_trade_percent).",
    parameter_type=ParameterType.FLOAT,
    minimum=0.5,
    maximum=2.0,
    step=0.5,
    default=1.0,
    safe_to_optimize=True,
)

MAX_TRADES_PER_DAY = OptimizableParameter(
    name="max_trades_per_day",
    description="Maximum trades permitted in a single trading day (RiskConfig.max_trades_per_day).",
    parameter_type=ParameterType.INT,
    minimum=1,
    maximum=10,
    step=1,
    default=5,
    safe_to_optimize=True,
)

DEFAULT_PARAMETER_CATALOG: tuple[OptimizableParameter, ...] = (
    EMA_PERIOD,
    RSI_BULLISH_THRESHOLD,
    RSI_BEARISH_THRESHOLD,
    REWARD_RISK_RATIO,
    RISK_PERCENT,
    MAX_TRADES_PER_DAY,
)
