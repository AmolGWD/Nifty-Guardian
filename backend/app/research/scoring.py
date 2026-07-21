"""
Configurable weighted scoring: each metric is min-max normalized
*across the batch of results being scored together* (there is no
universal scale a raw Net Profit figure and a raw Sharpe Ratio could
otherwise share), inverted first for metrics where lower is better
(Max Drawdown), then combined by the caller's weights. A metric with
no variance across the batch (or entirely missing) contributes nothing
rather than raising or dividing by zero.

Weights are used exactly as given - this module does not require them
to sum to 1.0/100%. A caller who wants a 0-1 or 0-100 final score is
responsible for normalizing their own weights; enforcing that here
would be an opinion this framework doesn't need to hold.
"""

from pydantic import BaseModel, ConfigDict

from app.research.models import LOWER_IS_BETTER, ExperimentResult, Metric, extract_metric


class ScoringWeights(BaseModel):
    model_config = ConfigDict(frozen=True)

    weights: dict[Metric, float]


def calculate_scores(
    results: list[ExperimentResult], weights: ScoringWeights
) -> dict[str, float]:
    scores: dict[str, float] = {result.experiment.experiment_id: 0.0 for result in results}

    for metric, weight in weights.weights.items():
        raw_values = {
            result.experiment.experiment_id: extract_metric(result, metric) for result in results
        }
        present_values = [value for value in raw_values.values() if value is not None]
        if not present_values:
            continue

        low, high = min(present_values), max(present_values)
        span = high - low if high != low else 1.0

        for result in results:
            value = raw_values[result.experiment.experiment_id]
            if value is None:
                continue

            normalized = (value - low) / span
            if metric in LOWER_IS_BETTER:
                normalized = 1 - normalized

            scores[result.experiment.experiment_id] += normalized * weight

    return scores
