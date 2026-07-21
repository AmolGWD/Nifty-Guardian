"""
Ranks experiments by a single configurable metric. Missing values
(a FAILED experiment, or a metric like Sharpe Ratio that Analytics
itself couldn't compute) always sort last, regardless of the metric's
direction - a result nothing can meaningfully compare against.
"""

from app.research.models import LOWER_IS_BETTER, ExperimentResult, Metric, extract_metric


def rank_experiments(results: list[ExperimentResult], metric: Metric) -> list[ExperimentResult]:
    lower_is_better = metric in LOWER_IS_BETTER

    def sort_key(result: ExperimentResult) -> tuple[int, float]:
        value = extract_metric(result, metric)
        if value is None:
            return (1, 0.0)
        return (0, value if lower_is_better else -value)

    return sorted(results, key=sort_key)
