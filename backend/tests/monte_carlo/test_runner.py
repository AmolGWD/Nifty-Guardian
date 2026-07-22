import pytest

from app.monte_carlo.models import PerturbationConfig
from app.monte_carlo.perturbations.execution_delay import ExecutionDelayConfig
from app.monte_carlo.perturbations.missed_trade import MissedTradeConfig
from app.monte_carlo.perturbations.slippage import SlippageConfig
from app.monte_carlo.runner import run_monte_carlo_simulation
from tests.monte_carlo.helpers import make_real_backtest_result


def test_produces_the_requested_number_of_simulations() -> None:
    backtest_result, _ = make_real_backtest_result()

    run = run_monte_carlo_simulation(
        backtest_result=backtest_result,
        perturbation_config=PerturbationConfig(),
        num_simulations=25,
        seed=1,
    )

    assert run.num_simulations == 25
    assert len(run.results) == 25


def test_simulation_indices_are_sequential() -> None:
    backtest_result, _ = make_real_backtest_result()

    run = run_monte_carlo_simulation(
        backtest_result=backtest_result,
        perturbation_config=PerturbationConfig(),
        num_simulations=10,
        seed=1,
    )

    assert [r.simulation_index for r in run.results] == list(range(10))


def test_baseline_metrics_come_from_the_original_backtest() -> None:
    backtest_result, _ = make_real_backtest_result()

    run = run_monte_carlo_simulation(
        backtest_result=backtest_result,
        perturbation_config=PerturbationConfig(),
        num_simulations=5,
        seed=1,
    )

    assert run.baseline_net_profit == backtest_result.report.net_profit
    assert run.baseline_max_drawdown == backtest_result.report.max_drawdown
    assert run.initial_capital == backtest_result.config.initial_capital


def test_no_perturbations_every_simulation_matches_the_original() -> None:
    backtest_result, _ = make_real_backtest_result()

    run = run_monte_carlo_simulation(
        backtest_result=backtest_result,
        perturbation_config=PerturbationConfig(),
        num_simulations=5,
        seed=1,
    )

    for result in run.results:
        assert result.net_profit == backtest_result.report.net_profit
        assert result.total_trades == backtest_result.report.total_trades


def test_same_seed_is_fully_deterministic() -> None:
    backtest_result, candles = make_real_backtest_result()
    config = PerturbationConfig(
        trade_shuffle_enabled=True,
        slippage=SlippageConfig(entry_slippage_percent=0.1, exit_slippage_percent=0.1),
        missed_trades=MissedTradeConfig(miss_probability_percent=10.0),
    )

    first = run_monte_carlo_simulation(
        backtest_result=backtest_result, perturbation_config=config,
        num_simulations=50, seed=42, candles=candles,
    )
    second = run_monte_carlo_simulation(
        backtest_result=backtest_result, perturbation_config=config,
        num_simulations=50, seed=42, candles=candles,
    )

    assert [r.net_profit for r in first.results] == [r.net_profit for r in second.results]
    assert [r.total_trades for r in first.results] == [r.total_trades for r in second.results]


def test_different_seeds_can_produce_different_results() -> None:
    backtest_result, candles = make_real_backtest_result()
    config = PerturbationConfig(
        trade_shuffle_enabled=True,
        missed_trades=MissedTradeConfig(miss_probability_percent=30.0),
    )

    first = run_monte_carlo_simulation(
        backtest_result=backtest_result, perturbation_config=config,
        num_simulations=50, seed=1, candles=candles,
    )
    second = run_monte_carlo_simulation(
        backtest_result=backtest_result, perturbation_config=config,
        num_simulations=50, seed=2, candles=candles,
    )

    first_trade_counts = [r.total_trades for r in first.results]
    second_trade_counts = [r.total_trades for r in second.results]
    assert first_trade_counts != second_trade_counts


def test_execution_delay_perturbation_works_end_to_end_with_real_candles() -> None:
    backtest_result, candles = make_real_backtest_result()

    run = run_monte_carlo_simulation(
        backtest_result=backtest_result,
        perturbation_config=PerturbationConfig(
            execution_delay=ExecutionDelayConfig(delay_candles=2)
        ),
        num_simulations=5,
        seed=1,
        candles=candles,
    )

    assert len(run.results) == 5


def test_rejects_non_positive_num_simulations() -> None:
    backtest_result, _ = make_real_backtest_result()

    with pytest.raises(ValueError, match="num_simulations"):
        run_monte_carlo_simulation(
            backtest_result=backtest_result, perturbation_config=PerturbationConfig(),
            num_simulations=0, seed=1,
        )
