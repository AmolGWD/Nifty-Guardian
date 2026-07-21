"""
Grid Search Strategy Optimization Engine domain models.

Every model here is a frozen Pydantic model (ADR-0006), same discipline
as every other domain package. This package calculates nothing itself -
`OptimizationResult` wraps an `ExperimentResult` produced by the
existing (frozen) `app.research.experiment_runner.run_experiment()`;
this module only defines the shapes needed to describe a grid search
run, not a second copy of backtest/analytics logic.

`GridValue` is `int | float` rather than the wider
`app.research.models.ParameterValue` - every parameter this package
optimizes is numeric (see `parameter_space.py`); there is no bool/str
dimension to support.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.optimization.parameter_space import ParameterSpace
from app.research.models import ExperimentResult, Metric

GridValue = int | float


class OptimizationResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    combination_id: str
    parameter_values: dict[str, GridValue]
    experiment_result: ExperimentResult
    failed: bool
    error: str | None = None


class OptimizationRun(BaseModel):
    model_config = ConfigDict(frozen=True)

    run_id: str
    created_date: datetime
    strategy_name: str
    dataset_path: str
    parameter_space: ParameterSpace
    results: tuple[OptimizationResult, ...]
    total_combinations: int
    failed_count: int
    duration_seconds: float


class RankedOptimizationResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    result: OptimizationResult
    rank: int
    score: float | None


class MetricDistribution(BaseModel):
    model_config = ConfigDict(frozen=True)

    metric: Metric
    minimum: float | None
    maximum: float | None
    mean: float | None
    median: float | None
    sample_size: int


class ParameterValueSummary(BaseModel):
    model_config = ConfigDict(frozen=True)

    parameter_name: str
    value: GridValue
    combinations_tested: int
    average_weighted_score: float | None


class OptimizationReport(BaseModel):
    model_config = ConfigDict(frozen=True)

    run_id: str
    total_combinations: int
    completed: int
    failed: int
    duration_seconds: float
    top_10: tuple[RankedOptimizationResult, ...]
    worst_10: tuple[RankedOptimizationResult, ...]
    parameter_summary: tuple[ParameterValueSummary, ...]
    metric_distributions: tuple[MetricDistribution, ...]


class OptimizationProgress(BaseModel):
    model_config = ConfigDict(frozen=True)

    total_combinations: int
    completed: int
    failed: int
    elapsed_seconds: float
    estimated_remaining_seconds: float | None

    @property
    def remaining(self) -> int:
        return self.total_combinations - self.completed
