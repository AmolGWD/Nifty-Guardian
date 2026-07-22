from app.optimization.parameter_space import OptimizableParameter, ParameterSpace, ParameterType
from app.validation.models import ValidationRules, WindowConfig, WindowStatus, WindowType
from app.validation.runner import run_walk_forward_validation
from tests.validation.helpers import make_base_backtest_config, make_synthetic_dataset

_RISK_PERCENT = OptimizableParameter(
    name="risk_percent",
    description="test",
    parameter_type=ParameterType.FLOAT,
    minimum=0.5,
    maximum=1.0,
    step=0.5,
    default=1.0,
    safe_to_optimize=True,
)

_PERMISSIVE_RULES = ValidationRules(
    max_drawdown_increase_percent=1000.0,
    min_profit_factor=0.0,
    max_performance_degradation_percent=1000.0,
    min_trade_count=0,
    min_robustness_score_percent=0.0,
)


def _window_config(**overrides: object) -> WindowConfig:
    base = dict(
        window_type=WindowType.ROLLING,
        training_duration_days=6,
        testing_duration_days=3,
        step_size_days=3,
        minimum_candles=20,
        minimum_trades=0,
    )
    base.update(overrides)
    return WindowConfig(**base)


def test_produces_one_result_per_generated_window() -> None:
    dataset_path = make_synthetic_dataset(14)
    space = ParameterSpace(parameters=(_RISK_PERCENT,))

    run = run_walk_forward_validation(
        window_config=_window_config(),
        parameter_space=space,
        validation_rules=_PERMISSIVE_RULES,
        dataset_path=dataset_path,
        base_backtest_config=make_base_backtest_config(),
    )

    assert len(run.results) > 0
    assert [r.window.window_index for r in run.results] == list(range(len(run.results)))


def test_completed_windows_have_both_train_and_test_results() -> None:
    dataset_path = make_synthetic_dataset(14)
    space = ParameterSpace(parameters=(_RISK_PERCENT,))

    run = run_walk_forward_validation(
        window_config=_window_config(),
        parameter_space=space,
        validation_rules=_PERMISSIVE_RULES,
        dataset_path=dataset_path,
        base_backtest_config=make_base_backtest_config(),
    )

    completed = [r for r in run.results if r.status == WindowStatus.COMPLETED]
    assert len(completed) > 0
    for result in completed:
        assert result.train_result is not None
        assert result.test_result is not None
        assert result.pass_fail is not None
        assert result.best_parameter_values is not None


def test_train_and_test_use_disjoint_non_overlapping_data() -> None:
    dataset_path = make_synthetic_dataset(14)
    space = ParameterSpace(parameters=(_RISK_PERCENT,))

    run = run_walk_forward_validation(
        window_config=_window_config(),
        parameter_space=space,
        validation_rules=_PERMISSIVE_RULES,
        dataset_path=dataset_path,
        base_backtest_config=make_base_backtest_config(),
    )

    for result in run.results:
        assert result.window.train_end <= result.window.test_start


def test_insufficient_candles_produces_insufficient_data_status() -> None:
    dataset_path = make_synthetic_dataset(14)
    space = ParameterSpace(parameters=(_RISK_PERCENT,))
    huge_minimum = _window_config(minimum_candles=100_000)

    run = run_walk_forward_validation(
        window_config=huge_minimum,
        parameter_space=space,
        validation_rules=_PERMISSIVE_RULES,
        dataset_path=dataset_path,
        base_backtest_config=make_base_backtest_config(),
    )

    assert len(run.results) > 0
    assert all(r.status == WindowStatus.INSUFFICIENT_DATA for r in run.results)


def test_insufficient_trades_produces_insufficient_data_status() -> None:
    dataset_path = make_synthetic_dataset(14)
    space = ParameterSpace(parameters=(_RISK_PERCENT,))
    unreachable_minimum_trades = _window_config(minimum_trades=100_000)

    run = run_walk_forward_validation(
        window_config=unreachable_minimum_trades,
        parameter_space=space,
        validation_rules=_PERMISSIVE_RULES,
        dataset_path=dataset_path,
        base_backtest_config=make_base_backtest_config(),
    )

    assert len(run.results) > 0
    assert all(r.status == WindowStatus.INSUFFICIENT_DATA for r in run.results)
    assert all(r.test_result is None for r in run.results)


def test_best_configuration_from_training_is_reused_for_testing() -> None:
    dataset_path = make_synthetic_dataset(14)
    space = ParameterSpace(parameters=(_RISK_PERCENT,))

    run = run_walk_forward_validation(
        window_config=_window_config(),
        parameter_space=space,
        validation_rules=_PERMISSIVE_RULES,
        dataset_path=dataset_path,
        base_backtest_config=make_base_backtest_config(),
    )

    completed = [r for r in run.results if r.status == WindowStatus.COMPLETED]
    assert completed
    for result in completed:
        assert result.train_result is not None
        assert result.test_result is not None
        train_config = result.train_result.experiment.backtest_config
        test_config = result.test_result.experiment.backtest_config
        assert train_config.risk_config == test_config.risk_config
        assert train_config.strategy_parameters == test_config.strategy_parameters


def test_no_randomization_same_inputs_same_outputs() -> None:
    dataset_path = make_synthetic_dataset(14)
    space = ParameterSpace(parameters=(_RISK_PERCENT,))
    config = make_base_backtest_config()

    first = run_walk_forward_validation(
        window_config=_window_config(), parameter_space=space,
        validation_rules=_PERMISSIVE_RULES, dataset_path=dataset_path,
        base_backtest_config=config,
    )
    second = run_walk_forward_validation(
        window_config=_window_config(), parameter_space=space,
        validation_rules=_PERMISSIVE_RULES, dataset_path=dataset_path,
        base_backtest_config=config,
    )

    first_profits = [
        r.train_result.backtest_result.report.net_profit
        for r in first.results
        if r.train_result and r.train_result.backtest_result
    ]
    second_profits = [
        r.train_result.backtest_result.report.net_profit
        for r in second.results
        if r.train_result and r.train_result.backtest_result
    ]
    assert first_profits == second_profits


def test_expanding_and_anchored_window_types_run_end_to_end() -> None:
    dataset_path = make_synthetic_dataset(14)
    space = ParameterSpace(parameters=(_RISK_PERCENT,))

    for window_type in (WindowType.EXPANDING, WindowType.ANCHORED):
        run = run_walk_forward_validation(
            window_config=_window_config(window_type=window_type),
            parameter_space=space,
            validation_rules=_PERMISSIVE_RULES,
            dataset_path=dataset_path,
            base_backtest_config=make_base_backtest_config(),
        )
        assert len(run.results) > 0
