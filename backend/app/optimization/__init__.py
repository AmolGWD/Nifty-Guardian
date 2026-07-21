"""
Grid Search Strategy Optimization Engine (Phase 16).

Orchestrates exhaustive parameter evaluation over the existing
(frozen) Strategy Experiment Framework - no AI, no strategy-logic
changes, no randomization. `optimizer.optimize()` is the one function
most callers need; see `docs/OPTIMIZATION_GUIDE.md` for the full guide.
"""

from app.optimization.models import (
    MetricDistribution,
    OptimizationProgress,
    OptimizationReport,
    OptimizationResult,
    OptimizationRun,
    ParameterValueSummary,
    RankedOptimizationResult,
)
from app.optimization.optimizer import optimize
from app.optimization.parameter_space import (
    DEFAULT_PARAMETER_CATALOG,
    OptimizableParameter,
    ParameterSpace,
    ParameterType,
)
from app.optimization.ranking import DEFAULT_SCORING_WEIGHTS, RankBy

__all__ = [
    "DEFAULT_PARAMETER_CATALOG",
    "DEFAULT_SCORING_WEIGHTS",
    "MetricDistribution",
    "OptimizableParameter",
    "OptimizationProgress",
    "OptimizationReport",
    "OptimizationResult",
    "OptimizationRun",
    "ParameterSpace",
    "ParameterType",
    "ParameterValueSummary",
    "RankBy",
    "RankedOptimizationResult",
    "optimize",
]
