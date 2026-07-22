import pytest

from app.monte_carlo.models import SimulationResult
from app.monte_carlo.statistics import compute_statistics


def _result(index: int, *, return_percent: float, drawdown: float = 0.0) -> SimulationResult:
    return SimulationResult(
        simulation_index=index,
        final_capital=100_000.0 * (1 + return_percent / 100),
        net_profit=100_000.0 * return_percent / 100,
        total_return_percent=return_percent,
        max_drawdown=drawdown,
        total_trades=5,
    )


def test_mean_and_median_return() -> None:
    results = [_result(i, return_percent=value) for i, value in enumerate([1.0, 2.0, 3.0])]

    stats = compute_statistics(results)

    assert stats.mean_return_percent == pytest.approx(2.0)
    assert stats.median_return_percent == pytest.approx(2.0)


def test_worst_and_best_return() -> None:
    results = [_result(i, return_percent=value) for i, value in enumerate([-5.0, 0.0, 10.0])]

    stats = compute_statistics(results)

    assert stats.worst_return_percent == -5.0
    assert stats.best_return_percent == 10.0


def test_worst_and_median_drawdown() -> None:
    results = [
        _result(0, return_percent=1.0, drawdown=100.0),
        _result(1, return_percent=1.0, drawdown=300.0),
        _result(2, return_percent=1.0, drawdown=200.0),
    ]

    stats = compute_statistics(results)

    assert stats.worst_drawdown == 300.0
    assert stats.median_drawdown == 200.0


def test_probability_of_profit_and_loss() -> None:
    results = [
        _result(i, return_percent=value)
        for i, value in enumerate([5.0, 5.0, -5.0, 0.0])
    ]

    stats = compute_statistics(results)

    assert stats.probability_of_profit_percent == pytest.approx(50.0)
    assert stats.probability_of_loss_percent == pytest.approx(25.0)


def test_all_profitable_gives_zero_var_and_cvar() -> None:
    results = [_result(i, return_percent=value) for i, value in enumerate([1.0, 2.0, 3.0, 4.0])]

    stats = compute_statistics(results)

    assert stats.value_at_risk_percent == 0.0
    assert stats.conditional_value_at_risk_percent == 0.0


def test_var_and_cvar_are_positive_when_losses_exist() -> None:
    results = [
        _result(i, return_percent=value)
        for i, value in enumerate([-20.0, -10.0, -5.0, 0.0, 5.0, 10.0, 15.0, 20.0, 25.0, 30.0])
    ]

    stats = compute_statistics(results)

    assert stats.value_at_risk_percent > 0
    assert stats.conditional_value_at_risk_percent >= stats.value_at_risk_percent


def test_confidence_interval_bounds_the_middle_of_the_distribution() -> None:
    results = [_result(i, return_percent=float(value)) for i, value in enumerate(range(100))]

    stats = compute_statistics(results, confidence_level_percent=95.0)

    assert stats.confidence_interval.confidence_level_percent == 95.0
    assert 0 < stats.confidence_interval.lower_bound < stats.confidence_interval.upper_bound < 99


def test_single_result_does_not_crash() -> None:
    stats = compute_statistics([_result(0, return_percent=5.0, drawdown=10.0)])

    assert stats.sample_size == 1
    assert stats.mean_return_percent == 5.0
    assert stats.std_dev_return_percent == 0.0


def test_empty_results_raises() -> None:
    with pytest.raises(ValueError, match="at least one"):
        compute_statistics([])
