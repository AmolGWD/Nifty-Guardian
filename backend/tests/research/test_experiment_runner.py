"""
Integration tests: run_experiment()/run_experiments() actually invoke
the real (frozen) Backtest Engine and Analytics Engine against the
sample CSV fixture - no mocking of either.
"""

from app.research.experiment_runner import run_experiment, run_experiments
from app.research.models import ExperimentResult, ExperimentStatus
from tests.research.helpers import make_backtest_config, make_test_experiment


def test_run_experiment_returns_a_completed_result() -> None:
    experiment = make_test_experiment()

    result = run_experiment(experiment)

    assert isinstance(result, ExperimentResult)
    assert result.status == ExperimentStatus.COMPLETED
    assert result.error is None
    assert result.backtest_result is not None
    assert result.analytics_report is not None
    assert result.duration_seconds is not None
    assert result.duration_seconds >= 0


def test_run_experiment_result_reuses_the_given_experiment() -> None:
    experiment = make_test_experiment(name="Reused")

    result = run_experiment(experiment)

    assert result.experiment == experiment


def test_run_experiment_fails_gracefully_on_a_bad_dataset_path() -> None:
    experiment = make_test_experiment(dataset_path="does_not_exist.csv")

    result = run_experiment(experiment)

    assert result.status == ExperimentStatus.FAILED
    assert result.error is not None
    assert result.backtest_result is None
    assert result.analytics_report is None


def test_run_experiments_runs_every_experiment_independently() -> None:
    good = make_test_experiment(name="Good")
    bad = make_test_experiment(name="Bad", dataset_path="does_not_exist.csv")

    results = run_experiments([good, bad])

    assert len(results) == 2
    assert results[0].status == ExperimentStatus.COMPLETED
    assert results[1].status == ExperimentStatus.FAILED


def test_two_experiments_with_different_risk_config_produce_different_results() -> None:
    conservative = make_test_experiment(
        name="Conservative", backtest_config=make_backtest_config(risk_per_trade_percent=0.5)
    )
    aggressive = make_test_experiment(
        name="Aggressive", backtest_config=make_backtest_config(risk_per_trade_percent=2.0)
    )

    conservative_result = run_experiment(conservative)
    aggressive_result = run_experiment(aggressive)

    assert conservative_result.status == ExperimentStatus.COMPLETED
    assert aggressive_result.status == ExperimentStatus.COMPLETED
    # Doubling risk-per-trade should at least change position sizing/PnL
    # magnitude versus the conservative run - not asserting a specific
    # direction, just that varying a real config parameter has an effect.
    assert (
        conservative_result.analytics_report.overall.net_profit  # type: ignore[union-attr]
        != aggressive_result.analytics_report.overall.net_profit  # type: ignore[union-attr]
    )
