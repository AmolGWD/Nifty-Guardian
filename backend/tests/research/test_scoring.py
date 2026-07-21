from app.research.models import ExperimentStatus, Metric
from app.research.scoring import ScoringWeights, calculate_scores
from tests.research.helpers import make_synthetic_result


def test_calculate_scores_matches_hand_calculated_values_for_two_experiments() -> None:
    # Two experiments, one metric (Net Profit), weight 1.0:
    # min=1000 (A), max=3000 (B) -> A normalizes to 0.0, B to 1.0.
    a = make_synthetic_result(name="A", net_profit=1000.0)
    b = make_synthetic_result(name="B", net_profit=3000.0)

    scores = calculate_scores([a, b], ScoringWeights(weights={Metric.NET_PROFIT: 1.0}))

    assert scores[a.experiment.experiment_id] == 0.0
    assert scores[b.experiment.experiment_id] == 1.0


def test_calculate_scores_inverts_lower_is_better_metrics() -> None:
    # Max Drawdown: lower is better, so the smaller drawdown should
    # score higher after inversion.
    small_dd = make_synthetic_result(name="SmallDD", max_drawdown=100.0)
    large_dd = make_synthetic_result(name="LargeDD", max_drawdown=900.0)

    scores = calculate_scores(
        [small_dd, large_dd], ScoringWeights(weights={Metric.MAX_DRAWDOWN: 1.0})
    )

    assert scores[small_dd.experiment.experiment_id] == 1.0
    assert scores[large_dd.experiment.experiment_id] == 0.0


def test_calculate_scores_combines_multiple_weighted_metrics() -> None:
    a = make_synthetic_result(name="A", net_profit=1000.0, win_rate=40.0)
    b = make_synthetic_result(name="B", net_profit=3000.0, win_rate=80.0)

    weights = ScoringWeights(weights={Metric.NET_PROFIT: 0.7, Metric.WIN_RATE: 0.3})
    scores = calculate_scores([a, b], weights)

    # A is worst on both metrics (normalized 0.0 on each) -> total 0.0
    # B is best on both (normalized 1.0 on each) -> total 0.7 + 0.3 = 1.0
    assert scores[a.experiment.experiment_id] == 0.0
    assert scores[b.experiment.experiment_id] == 1.0


def test_calculate_scores_gives_zero_contribution_when_metric_has_no_variance() -> None:
    a = make_synthetic_result(name="A", net_profit=1000.0)
    b = make_synthetic_result(name="B", net_profit=1000.0)

    scores = calculate_scores([a, b], ScoringWeights(weights={Metric.NET_PROFIT: 1.0}))

    assert scores[a.experiment.experiment_id] == 0.0
    assert scores[b.experiment.experiment_id] == 0.0


def test_calculate_scores_skips_missing_values() -> None:
    good = make_synthetic_result(name="Good", net_profit=1000.0)
    failed = make_synthetic_result(name="Failed", status=ExperimentStatus.FAILED)

    scores = calculate_scores([good, failed], ScoringWeights(weights={Metric.NET_PROFIT: 1.0}))

    assert scores[failed.experiment.experiment_id] == 0.0
