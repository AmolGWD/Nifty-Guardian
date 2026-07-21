"""
In-memory registry of experiments and their results - mirrors
`app.trading.strategy.registry.StrategyRegistry`'s pattern (Phase 8)
and `app.data.repository.HistoricalDataRepository`'s (Phase 13):
register, then look up by id, list all, or filter by tag. No database
this phase, consistent with every other in-memory store already built.
"""

from app.research.models import Experiment, ExperimentResult


class ExperimentRegistry:
    def __init__(self) -> None:
        self._experiments: dict[str, Experiment] = {}
        self._results: dict[str, ExperimentResult] = {}

    def register(self, experiment: Experiment) -> None:
        self._experiments[experiment.experiment_id] = experiment

    def record_result(self, result: ExperimentResult) -> None:
        self._experiments[result.experiment.experiment_id] = result.experiment
        self._results[result.experiment.experiment_id] = result

    def get_experiment(self, experiment_id: str) -> Experiment | None:
        return self._experiments.get(experiment_id)

    def get_result(self, experiment_id: str) -> ExperimentResult | None:
        return self._results.get(experiment_id)

    def all_experiments(self) -> list[Experiment]:
        return list(self._experiments.values())

    def all_results(self) -> list[ExperimentResult]:
        return list(self._results.values())

    def find_by_tag(self, tag: str) -> list[Experiment]:
        return [experiment for experiment in self._experiments.values() if tag in experiment.tags]
