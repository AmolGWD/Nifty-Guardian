"""
Walk-Forward Validation Framework domain models.

Every model here is a frozen Pydantic model (ADR-0006). This package
calculates nothing itself beyond the pass/fail rule comparisons in
`validator.py` - `ValidationResult` wraps two `ExperimentResult`s
(train, test) produced by the existing (frozen) `app.research`/
`app.trading.backtest`/`app.trading.analytics`, and `OptimizationRun`
produced by the existing (frozen) `app.optimization`.
"""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, model_validator

from app.config.validation import ParameterValidationError
from app.optimization.models import GridValue
from app.research.models import ExperimentResult


class WindowType(StrEnum):
    ROLLING = "Rolling"
    EXPANDING = "Expanding"
    ANCHORED = "Anchored"


class Window(BaseModel):
    model_config = ConfigDict(frozen=True)

    window_index: int
    train_start: datetime
    train_end: datetime
    test_start: datetime
    test_end: datetime


class WindowConfig(BaseModel):
    model_config = ConfigDict(frozen=True)

    window_type: WindowType
    training_duration_days: int
    testing_duration_days: int
    step_size_days: int
    minimum_candles: int
    minimum_trades: int

    @model_validator(mode="after")
    def _validate(self) -> "WindowConfig":
        if self.training_duration_days <= 0:
            raise ParameterValidationError("training_duration_days must be positive")
        if self.testing_duration_days <= 0:
            raise ParameterValidationError("testing_duration_days must be positive")
        if self.step_size_days <= 0:
            raise ParameterValidationError("step_size_days must be positive")
        if self.minimum_candles < 0:
            raise ParameterValidationError("minimum_candles cannot be negative")
        if self.minimum_trades < 0:
            raise ParameterValidationError("minimum_trades cannot be negative")
        return self


class ValidationRules(BaseModel):
    """
    Every threshold here must be supplied by the caller - see
    `docs/VALIDATION_GUIDE.md`'s "Recommended defaults" for suggested
    starting values that are documented, not hardcoded into this model.
    """

    model_config = ConfigDict(frozen=True)

    max_drawdown_increase_percent: float
    min_profit_factor: float
    max_performance_degradation_percent: float
    min_trade_count: int
    min_robustness_score_percent: float

    @model_validator(mode="after")
    def _validate(self) -> "ValidationRules":
        if self.max_drawdown_increase_percent < 0:
            raise ParameterValidationError("max_drawdown_increase_percent cannot be negative")
        if self.min_profit_factor < 0:
            raise ParameterValidationError("min_profit_factor cannot be negative")
        if self.max_performance_degradation_percent < 0:
            raise ParameterValidationError(
                "max_performance_degradation_percent cannot be negative"
            )
        if self.min_trade_count < 0:
            raise ParameterValidationError("min_trade_count cannot be negative")
        if not (0 <= self.min_robustness_score_percent <= 100):
            raise ParameterValidationError(
                "min_robustness_score_percent must be within [0, 100]"
            )
        return self


class RuleEvaluation(BaseModel):
    model_config = ConfigDict(frozen=True)

    rule_name: str
    passed: bool
    detail: str


class PassFailAssessment(BaseModel):
    model_config = ConfigDict(frozen=True)

    passed: bool
    evaluations: tuple[RuleEvaluation, ...]


class WindowStatus(StrEnum):
    COMPLETED = "Completed"
    INSUFFICIENT_DATA = "InsufficientData"
    FAILED = "Failed"


class ValidationResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    window: Window
    status: WindowStatus
    best_parameter_values: dict[str, GridValue] | None
    train_result: ExperimentResult | None
    test_result: ExperimentResult | None
    pass_fail: PassFailAssessment | None
    error: str | None = None


class ValidationRun(BaseModel):
    model_config = ConfigDict(frozen=True)

    run_id: str
    created_date: datetime
    strategy_name: str
    dataset_path: str
    window_config: WindowConfig
    validation_rules: ValidationRules
    results: tuple[ValidationResult, ...]
    duration_seconds: float


class WindowSummary(BaseModel):
    model_config = ConfigDict(frozen=True)

    window_index: int
    status: WindowStatus
    train_start: datetime
    train_end: datetime
    test_start: datetime
    test_end: datetime
    best_parameter_values: dict[str, GridValue] | None
    train_net_profit: float | None
    test_net_profit: float | None
    train_win_rate: float | None
    test_win_rate: float | None
    train_profit_factor: float | None
    test_profit_factor: float | None
    train_max_drawdown: float | None
    test_max_drawdown: float | None
    performance_degradation_percent: float | None
    passed: bool | None


class MetricStabilitySummary(BaseModel):
    model_config = ConfigDict(frozen=True)

    metric_name: str
    train_values: tuple[float, ...]
    test_values: tuple[float, ...]
    train_mean: float | None
    test_mean: float | None


class ParameterStability(BaseModel):
    model_config = ConfigDict(frozen=True)

    parameter_name: str
    values_chosen: tuple[GridValue, ...]
    distinct_value_count: int
    most_common_value: GridValue | None
    most_common_value_frequency: float | None


class ValidationReport(BaseModel):
    model_config = ConfigDict(frozen=True)

    run_id: str
    total_windows: int
    completed_windows: int
    insufficient_data_windows: int
    failed_windows: int
    passed_windows: int
    robustness_score: float
    overall_passed: bool
    window_summaries: tuple[WindowSummary, ...]
    parameter_stability: tuple[ParameterStability, ...]
    average_performance_degradation_percent: float | None
    performance_degradation: MetricStabilitySummary
    drawdown_comparison: MetricStabilitySummary
    equity_comparison: MetricStabilitySummary
    win_rate_stability: MetricStabilitySummary
    profit_factor_stability: MetricStabilitySummary
