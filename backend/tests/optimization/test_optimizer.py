from app.optimization.optimizer import optimize
from app.optimization.parameter_space import OptimizableParameter, ParameterSpace, ParameterType
from app.optimization.ranking import RankBy
from app.trading.backtest.models import BacktestConfig
from app.trading.risk.models import RiskConfig
from tests.research.helpers import SAMPLE_CSV

_RISK_PERCENT_SMALL = OptimizableParameter(
    name="risk_percent",
    description="test",
    parameter_type=ParameterType.FLOAT,
    minimum=0.5,
    maximum=1.5,
    step=0.5,
    default=1.0,
    safe_to_optimize=True,
)


def test_optimize_end_to_end_returns_run_ranking_and_report() -> None:
    space = ParameterSpace(parameters=(_RISK_PERCENT_SMALL,))
    base_config = BacktestConfig(initial_capital=100_000.0, risk_config=RiskConfig())

    run, ranked, report = optimize(
        parameter_space=space, dataset_path=str(SAMPLE_CSV), base_backtest_config=base_config
    )

    assert run.total_combinations == 3
    assert len(ranked) == 3
    assert report.total_combinations == 3
    assert [r.rank for r in ranked] == [1, 2, 3]


def test_optimize_best_configuration_is_ranked_first() -> None:
    space = ParameterSpace(parameters=(_RISK_PERCENT_SMALL,))
    base_config = BacktestConfig(initial_capital=100_000.0, risk_config=RiskConfig())

    _, ranked, report = optimize(
        parameter_space=space,
        dataset_path=str(SAMPLE_CSV),
        base_backtest_config=base_config,
        rank_by=RankBy.NET_PROFIT,
    )

    best = ranked[0]
    assert best.rank == 1
    assert report.top_10[0].result.combination_id == best.result.combination_id


def test_optimize_supports_ranking_by_each_supported_metric() -> None:
    space = ParameterSpace(parameters=(_RISK_PERCENT_SMALL,))
    base_config = BacktestConfig(initial_capital=100_000.0, risk_config=RiskConfig())

    for rank_by in RankBy:
        _, ranked, _ = optimize(
            parameter_space=space,
            dataset_path=str(SAMPLE_CSV),
            base_backtest_config=base_config,
            rank_by=rank_by,
        )
        assert len(ranked) == 3
