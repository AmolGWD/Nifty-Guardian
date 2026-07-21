"""
Exports the flat, per-combination table (one row per OptimizationResult)
to Markdown/CSV/JSON. Every row's columns come entirely from
`app.research.export` - this module does not reimplement CSV/JSON/
Markdown writing, it only unwraps `OptimizationResult.experiment_result`
and passes the list straight through. Each combination's grid values
are already present on `Experiment.parameters` (set by `executor.py`),
so they show up automatically as `param_<name>` columns/fields, exactly
like every other experiment's parameters would.

For the aggregate report (top/worst configurations, parameter summary,
metric distributions) see `report.py` - a different artifact from this
flat table, matching the CTO brief's separate REPORT/EXPORT sections.
"""

from pathlib import Path

from app.optimization.models import OptimizationResult, RankedOptimizationResult
from app.research.export import export_csv as _export_experiment_csv
from app.research.export import export_json as _export_experiment_json
from app.research.export import export_markdown as _export_experiment_markdown
from app.research.models import ExperimentResult


def export_csv(
    results: list[OptimizationResult],
    path: str | Path,
    *,
    ranking: list[RankedOptimizationResult] | None = None,
) -> None:
    _export_experiment_csv(
        [result.experiment_result for result in results],
        path,
        ranking=_ranking_experiment_results(ranking),
    )


def export_json(
    results: list[OptimizationResult],
    path: str | Path,
    *,
    ranking: list[RankedOptimizationResult] | None = None,
) -> None:
    _export_experiment_json(
        [result.experiment_result for result in results],
        path,
        ranking=_ranking_experiment_results(ranking),
    )


def export_markdown(
    results: list[OptimizationResult],
    path: str | Path,
    *,
    ranking: list[RankedOptimizationResult] | None = None,
) -> None:
    _export_experiment_markdown(
        [result.experiment_result for result in results],
        path,
        ranking=_ranking_experiment_results(ranking),
    )


def _ranking_experiment_results(
    ranking: list[RankedOptimizationResult] | None,
) -> list[ExperimentResult] | None:
    if ranking is None:
        return None
    return [ranked_result.result.experiment_result for ranked_result in ranking]
