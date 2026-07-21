"""
Compares multiple ExperimentResults side by side against a chosen set
of metrics, reading each through `models.extract_metric()` - the one
shared mapping onto `AnalyticsReport.overall`, also used by
`ranking.py` and `scoring.py`.
"""

from pydantic import BaseModel, ConfigDict

from app.research.models import ExperimentResult, Metric, extract_metric


class ExperimentComparison(BaseModel):
    model_config = ConfigDict(frozen=True)

    experiment_id: str
    name: str
    metrics: dict[Metric, float | None]


def compare_experiments(
    results: list[ExperimentResult], metrics: list[Metric]
) -> list[ExperimentComparison]:
    return [
        ExperimentComparison(
            experiment_id=result.experiment.experiment_id,
            name=result.experiment.name,
            metrics={metric: extract_metric(result, metric) for metric in metrics},
        )
        for result in results
    ]
