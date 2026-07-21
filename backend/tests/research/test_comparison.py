from app.research.comparison import compare_experiments
from app.research.models import ExperimentStatus, Metric
from tests.research.helpers import make_synthetic_result


def test_compare_experiments_extracts_requested_metrics() -> None:
    a = make_synthetic_result(name="A", net_profit=1000.0, profit_factor=2.0)
    b = make_synthetic_result(name="B", net_profit=2000.0, profit_factor=1.5)

    comparisons = compare_experiments([a, b], [Metric.NET_PROFIT, Metric.PROFIT_FACTOR])

    by_name = {c.name: c for c in comparisons}
    assert by_name["A"].metrics == {Metric.NET_PROFIT: 1000.0, Metric.PROFIT_FACTOR: 2.0}
    assert by_name["B"].metrics == {Metric.NET_PROFIT: 2000.0, Metric.PROFIT_FACTOR: 1.5}


def test_compare_experiments_handles_missing_analytics_report() -> None:
    failed = make_synthetic_result(name="Failed", status=ExperimentStatus.FAILED)

    comparisons = compare_experiments([failed], [Metric.NET_PROFIT])

    assert comparisons[0].metrics[Metric.NET_PROFIT] is None


def test_compare_experiments_preserves_experiment_identity() -> None:
    result = make_synthetic_result(name="Solo")

    comparisons = compare_experiments([result], [Metric.NET_PROFIT])

    assert comparisons[0].experiment_id == result.experiment.experiment_id
