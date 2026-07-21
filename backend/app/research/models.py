"""
Strategy Experiment Framework domain models.

`Experiment` is the immutable *definition* of a run - what to test,
against what data, with what configuration - created once via
`experiment.create_experiment()`. `ExperimentResult` is produced by
actually running one (`experiment_runner.run_experiment()`): the
`Experiment` plus its outcome. These are deliberately two frozen types
rather than one mutable record, for the same reason every other
domain model in this codebase is frozen (ADR-0006) - `Experiment`
itself never changes after creation; running it produces a new,
separate, immutable result.

`Experiment.dataset_path` is named that, not `dataset`, specifically to
avoid confusion with `app.data.models.Dataset` (Phase 13) - this
platform's own stored-data type. Backtesting still reads a CSV path
directly (Phase 11, frozen; the migration to `app.data` was explicitly
deferred as later, separately-reviewed work in that phase's own
summary), so this framework does the same rather than quietly
performing that migration itself.

`Experiment.parameters` is a free-form, opaque bag - "EMA Period",
"RSI Threshold", and the rest of the brief's examples are stored and
exported, never interpreted. The two things this framework actually
uses to run a backtest are `backtest_config`/its nested `risk_config` -
the real, existing configuration surface the frozen Backtest Engine
already accepts. Today's frozen `EMABreakoutStrategy` has no
parameterization hook at all (its RSI thresholds are module-level
constants) - wiring arbitrary strategy parameters through is explicitly
Strategy Optimization's job (the next phase, not this one), so
`parameters` stays inert metadata until that phase gives it something
real to drive.
"""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict

from app.data.models import Timeframe
from app.trading.analytics.models import AnalyticsReport
from app.trading.backtest.models import BacktestConfig, BacktestResult

ParameterValue = str | int | float | bool


class ExperimentStatus(StrEnum):
    PENDING = "Pending"
    RUNNING = "Running"
    COMPLETED = "Completed"
    FAILED = "Failed"


class Experiment(BaseModel):
    model_config = ConfigDict(frozen=True)

    experiment_id: str
    name: str
    description: str
    created_date: datetime

    strategy: str
    dataset_path: str
    timeframe: Timeframe
    parameters: dict[str, ParameterValue]
    seed: int | None = None

    backtest_config: BacktestConfig

    tags: list[str] = []
    notes: str = ""
    git_commit_hash: str | None = None


class ExperimentResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    experiment: Experiment
    status: ExperimentStatus
    duration_seconds: float | None
    backtest_result: BacktestResult | None
    analytics_report: AnalyticsReport | None
    error: str | None = None


class Metric(StrEnum):
    """
    The shared vocabulary `comparison.py`, `ranking.py`, and
    `scoring.py` all read `ExperimentResult.analytics_report.overall`
    through - one mapping (`extract_metric` below), not three.
    """

    NET_PROFIT = "NetProfit"
    PROFIT_FACTOR = "ProfitFactor"
    EXPECTANCY = "Expectancy"
    MAX_DRAWDOWN = "MaxDrawdown"
    RECOVERY_FACTOR = "RecoveryFactor"
    SHARPE_RATIO = "SharpeRatio"
    CALMAR_RATIO = "CalmarRatio"
    WIN_RATE = "WinRate"


LOWER_IS_BETTER: frozenset[Metric] = frozenset({Metric.MAX_DRAWDOWN})


def extract_metric(result: ExperimentResult, metric: Metric) -> float | None:
    if result.analytics_report is None:
        return None

    overall = result.analytics_report.overall
    return {
        Metric.NET_PROFIT: overall.net_profit,
        Metric.PROFIT_FACTOR: overall.profit_factor,
        Metric.EXPECTANCY: overall.expectancy,
        Metric.MAX_DRAWDOWN: overall.max_drawdown,
        Metric.RECOVERY_FACTOR: overall.recovery_factor,
        Metric.SHARPE_RATIO: overall.sharpe_ratio,
        Metric.CALMAR_RATIO: overall.calmar_ratio,
        Metric.WIN_RATE: overall.win_rate,
    }[metric]
