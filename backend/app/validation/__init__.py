"""
Walk-Forward Validation Framework (Phase 17).

Evaluates whether an optimized configuration generalizes to unseen
market data - trains (via the existing Grid Search Optimization
Engine) on one window of history and tests the winning configuration
(via the existing Experiment/Backtest/Analytics Engines) on the very
next window, repeated across many windows. This is not another
optimizer; it orchestrates optimization and validation. See
`docs/VALIDATION_GUIDE.md` for the full guide.
"""

from app.validation.models import (
    MetricStabilitySummary,
    ParameterStability,
    PassFailAssessment,
    RuleEvaluation,
    ValidationReport,
    ValidationResult,
    ValidationRules,
    ValidationRun,
    Window,
    WindowConfig,
    WindowStatus,
    WindowSummary,
    WindowType,
)
from app.validation.runner import run_walk_forward_validation
from app.validation.window_generator import generate_windows

__all__ = [
    "MetricStabilitySummary",
    "ParameterStability",
    "PassFailAssessment",
    "RuleEvaluation",
    "ValidationReport",
    "ValidationResult",
    "ValidationRules",
    "ValidationRun",
    "Window",
    "WindowConfig",
    "WindowStatus",
    "WindowSummary",
    "WindowType",
    "generate_windows",
    "run_walk_forward_validation",
]
