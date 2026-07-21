from app.optimization.executor import run_grid_search
from app.optimization.models import OptimizationResult
from app.optimization.parameter_space import (
    MAX_TRADES_PER_DAY,
    REWARD_RISK_RATIO,
    RISK_PERCENT,
    OptimizableParameter,
    ParameterSpace,
    ParameterType,
)
from app.trading.backtest.models import BacktestConfig
from app.trading.risk.models import RiskConfig
from tests.research.helpers import SAMPLE_CSV


def _net_profits(results: tuple[OptimizationResult, ...]) -> list[float]:
    profits = []
    for result in results:
        backtest_result = result.experiment_result.backtest_result
        assert backtest_result is not None
        profits.append(backtest_result.report.net_profit)
    return profits

_SMALL_RR = OptimizableParameter(
    name="reward_risk_ratio",
    description="test",
    parameter_type=ParameterType.FLOAT,
    minimum=1.5,
    maximum=2.0,
    step=0.5,
    default=2.0,
    safe_to_optimize=True,
)


def _base_config() -> BacktestConfig:
    return BacktestConfig(initial_capital=100_000.0, risk_config=RiskConfig())


def test_run_grid_search_produces_one_result_per_combination() -> None:
    space = ParameterSpace(parameters=(_SMALL_RR,))

    run = run_grid_search(
        parameter_space=space, dataset_path=str(SAMPLE_CSV), base_backtest_config=_base_config()
    )

    assert run.total_combinations == 2
    assert len(run.results) == 2
    assert run.failed_count == 0


def test_combination_ids_are_deterministic_and_zero_padded() -> None:
    space = ParameterSpace(parameters=(_SMALL_RR,))

    run = run_grid_search(
        parameter_space=space, dataset_path=str(SAMPLE_CSV), base_backtest_config=_base_config()
    )

    assert [result.combination_id for result in run.results] == ["combo-0000", "combo-0001"]


def test_reward_risk_ratio_genuinely_changes_target_atr_multiplier() -> None:
    space = ParameterSpace(parameters=(_SMALL_RR,))
    base_config = _base_config()

    run = run_grid_search(
        parameter_space=space, dataset_path=str(SAMPLE_CSV), base_backtest_config=base_config
    )

    base_stop_multiplier = base_config.risk_config.stop_loss_atr_multiplier
    for result in run.results:
        rr = result.parameter_values["reward_risk_ratio"]
        risk_config = result.experiment_result.experiment.backtest_config.risk_config
        assert risk_config.target_atr_multiplier == rr * base_stop_multiplier


def test_reward_risk_ratio_genuinely_changes_net_profit() -> None:
    space = ParameterSpace(parameters=(REWARD_RISK_RATIO,))

    run = run_grid_search(
        parameter_space=space, dataset_path=str(SAMPLE_CSV), base_backtest_config=_base_config()
    )

    net_profits = set()
    for result in run.results:
        backtest_result = result.experiment_result.backtest_result
        assert backtest_result is not None
        net_profits.add(backtest_result.report.net_profit)
    assert len(net_profits) > 1


def test_risk_percent_and_max_trades_per_day_genuinely_reach_risk_config() -> None:
    space = ParameterSpace(parameters=(RISK_PERCENT, MAX_TRADES_PER_DAY))

    run = run_grid_search(
        parameter_space=space, dataset_path=str(SAMPLE_CSV), base_backtest_config=_base_config()
    )

    for result in run.results:
        risk_config = result.experiment_result.experiment.backtest_config.risk_config
        assert risk_config.risk_per_trade_percent == result.parameter_values["risk_percent"]
        assert risk_config.max_trades_per_day == result.parameter_values["max_trades_per_day"]


def test_ema_period_reaching_indicator_engine_produces_a_failed_result_when_too_small() -> None:
    """A larger ema_period than available warmup history fails that one combination,
    not the whole run - proving ema_period genuinely reaches calculate_indicator_snapshot."""
    tiny_ema = OptimizableParameter(
        name="ema_period", description="test", parameter_type=ParameterType.INT,
        minimum=200, maximum=201, step=1, default=200, safe_to_optimize=True,
    )
    space = ParameterSpace(parameters=(tiny_ema,))

    run = run_grid_search(
        parameter_space=space, dataset_path=str(SAMPLE_CSV), base_backtest_config=_base_config()
    )

    assert run.failed_count == 2
    assert all("EMA" in (result.error or "") for result in run.results)


def test_experiment_parameters_records_the_grid_combination() -> None:
    space = ParameterSpace(parameters=(_SMALL_RR,))

    run = run_grid_search(
        parameter_space=space, dataset_path=str(SAMPLE_CSV), base_backtest_config=_base_config()
    )

    for result in run.results:
        assert result.experiment_result.experiment.parameters == result.parameter_values


def test_run_grid_search_no_randomization_same_inputs_same_outputs() -> None:
    space = ParameterSpace(parameters=(RISK_PERCENT,))
    config = _base_config()

    first = run_grid_search(
        parameter_space=space, dataset_path=str(SAMPLE_CSV), base_backtest_config=config
    )
    second = run_grid_search(
        parameter_space=space, dataset_path=str(SAMPLE_CSV), base_backtest_config=config
    )

    first_profits = _net_profits(first.results)
    second_profits = _net_profits(second.results)
    assert first_profits == second_profits
