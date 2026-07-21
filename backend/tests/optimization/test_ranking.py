from app.optimization.ranking import RankBy, rank_optimization_results
from app.research.models import Metric
from app.research.scoring import ScoringWeights
from tests.optimization.helpers import make_optimization_result


def test_rank_by_net_profit() -> None:
    results = [
        make_optimization_result(combination_id="low", net_profit=100.0),
        make_optimization_result(combination_id="high", net_profit=900.0),
    ]

    ranked = rank_optimization_results(results, rank_by=RankBy.NET_PROFIT)

    assert [r.result.combination_id for r in ranked] == ["high", "low"]
    assert ranked[0].rank == 1
    assert ranked[0].score == 900.0


def test_rank_by_max_drawdown_prefers_lower() -> None:
    results = [
        make_optimization_result(combination_id="shallow", max_drawdown=100.0),
        make_optimization_result(combination_id="deep", max_drawdown=900.0),
    ]

    ranked = rank_optimization_results(results, rank_by=RankBy.MAX_DRAWDOWN)

    assert [r.result.combination_id for r in ranked] == ["shallow", "deep"]


def test_failed_results_sort_last_regardless_of_metric() -> None:
    results = [
        make_optimization_result(combination_id="ok", net_profit=1.0),
        make_optimization_result(combination_id="failed", failed=True),
    ]

    ranked = rank_optimization_results(results, rank_by=RankBy.NET_PROFIT)

    assert [r.result.combination_id for r in ranked] == ["ok", "failed"]
    assert ranked[-1].score is None


def test_weighted_score_default_ranking() -> None:
    results = [
        make_optimization_result(
            combination_id="better", profit_factor=3.0, sharpe_ratio=2.0,
            recovery_factor=3.0, win_rate=70.0,
        ),
        make_optimization_result(
            combination_id="worse", profit_factor=1.0, sharpe_ratio=0.5,
            recovery_factor=1.0, win_rate=30.0,
        ),
    ]

    ranked = rank_optimization_results(results)

    assert [r.result.combination_id for r in ranked] == ["better", "worse"]
    assert ranked[0].score is not None
    assert ranked[1].score is not None
    assert ranked[0].score > ranked[1].score


def test_weighted_score_accepts_custom_weights() -> None:
    results = [
        make_optimization_result(combination_id="a", net_profit=1000.0, win_rate=10.0),
        make_optimization_result(combination_id="b", net_profit=1.0, win_rate=90.0),
    ]

    weights = ScoringWeights(weights={Metric.WIN_RATE: 1.0})
    ranked = rank_optimization_results(results, weights=weights)

    assert ranked[0].result.combination_id == "b"


def test_rank_is_one_indexed_and_sequential() -> None:
    results = [
        make_optimization_result(combination_id=f"c{i}", net_profit=float(i)) for i in range(4)
    ]

    ranked = rank_optimization_results(results, rank_by=RankBy.NET_PROFIT)

    assert [r.rank for r in ranked] == [1, 2, 3, 4]
