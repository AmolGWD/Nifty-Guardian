"""
Executes one Experiment: load the dataset, invoke the existing
(frozen) Backtest Engine, invoke the existing (frozen) Analytics
Engine, and package the outcome into an ExperimentResult. This module
calculates nothing itself - it only orchestrates calls into Phase 11's
`run_backtest()` and Phase 12's `build_analytics_report()`, exactly as
those two phases orchestrate the packages beneath them.

A failure anywhere in that chain (bad parameters, too few candles in
the dataset, ...) is a real, expected outcome when running many
experiments - not an impossible scenario - so it's caught and returned
as a FAILED ExperimentResult with the error message recorded, rather
than raising and aborting whatever batch of experiments called this.
"""

import time

from app.research.models import Experiment, ExperimentResult, ExperimentStatus
from app.trading.analytics.analytics_engine import build_analytics_report
from app.trading.backtest.backtest_engine import run_backtest
from app.trading.backtest.loader import load_candles_from_csv


def run_experiment(experiment: Experiment) -> ExperimentResult:
    start = time.perf_counter()

    try:
        candles = load_candles_from_csv(experiment.dataset_path)
        backtest_result = run_backtest(candles, experiment.backtest_config)
        analytics_report = build_analytics_report(backtest_result, candles)
    except Exception as error:
        duration = time.perf_counter() - start
        return ExperimentResult(
            experiment=experiment,
            status=ExperimentStatus.FAILED,
            duration_seconds=duration,
            backtest_result=None,
            analytics_report=None,
            error=str(error),
        )

    duration = time.perf_counter() - start
    return ExperimentResult(
        experiment=experiment,
        status=ExperimentStatus.COMPLETED,
        duration_seconds=duration,
        backtest_result=backtest_result,
        analytics_report=analytics_report,
        error=None,
    )


def run_experiments(experiments: list[Experiment]) -> list[ExperimentResult]:
    return [run_experiment(experiment) for experiment in experiments]
