from app.research.models import ExperimentStatus, Metric
from app.research.ranking import rank_experiments
from tests.research.helpers import make_synthetic_result


def test_rank_by_net_profit_highest_first() -> None:
    low = make_synthetic_result(name="Low", net_profit=500.0)
    high = make_synthetic_result(name="High", net_profit=5000.0)
    mid = make_synthetic_result(name="Mid", net_profit=2000.0)

    ranked = rank_experiments([low, high, mid], Metric.NET_PROFIT)

    assert [r.experiment.name for r in ranked] == ["High", "Mid", "Low"]


def test_rank_by_max_drawdown_lowest_first() -> None:
    small_dd = make_synthetic_result(name="SmallDD", max_drawdown=100.0)
    large_dd = make_synthetic_result(name="LargeDD", max_drawdown=1000.0)

    ranked = rank_experiments([large_dd, small_dd], Metric.MAX_DRAWDOWN)

    assert [r.experiment.name for r in ranked] == ["SmallDD", "LargeDD"]


def test_rank_puts_missing_metric_values_last() -> None:
    good = make_synthetic_result(name="Good", net_profit=1000.0)
    failed = make_synthetic_result(name="Failed", status=ExperimentStatus.FAILED)

    ranked = rank_experiments([failed, good], Metric.NET_PROFIT)

    assert [r.experiment.name for r in ranked] == ["Good", "Failed"]


def test_rank_with_all_missing_values_preserves_stable_order() -> None:
    a = make_synthetic_result(name="A", status=ExperimentStatus.FAILED)
    b = make_synthetic_result(name="B", status=ExperimentStatus.FAILED)

    ranked = rank_experiments([a, b], Metric.NET_PROFIT)

    assert [r.experiment.name for r in ranked] == ["A", "B"]
