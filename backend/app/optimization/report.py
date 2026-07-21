"""
Builds an OptimizationReport (top/worst configurations, per-parameter
summary, metric distributions, run statistics) from a completed
OptimizationRun, and renders it to Markdown for print/export.

Failed combinations are excluded from every metric-based section here
(they have no AnalyticsReport to summarize) but are still counted in
the run statistics - a failed combination is a real, expected outcome
when running many experiments (see `app.research.experiment_runner`'s
own docstring), not something to hide.
"""

import statistics

from app.optimization.models import (
    GridValue,
    MetricDistribution,
    OptimizationReport,
    OptimizationResult,
    OptimizationRun,
    ParameterValueSummary,
    RankedOptimizationResult,
)
from app.optimization.ranking import DEFAULT_SCORING_WEIGHTS, RankBy, rank_optimization_results
from app.research.models import Metric, extract_metric
from app.research.scoring import ScoringWeights

_TOP_N = 10


def build_optimization_report(
    run: OptimizationRun,
    *,
    rank_by: RankBy = RankBy.WEIGHTED_SCORE,
    weights: ScoringWeights | None = None,
) -> OptimizationReport:
    completed_results = [result for result in run.results if not result.failed]
    ranked = rank_optimization_results(
        completed_results, rank_by=rank_by, weights=weights or DEFAULT_SCORING_WEIGHTS
    )

    top_10 = tuple(ranked[:_TOP_N])
    worst_10 = tuple(reversed(ranked[-_TOP_N:])) if ranked else ()

    return OptimizationReport(
        run_id=run.run_id,
        total_combinations=run.total_combinations,
        completed=run.total_combinations - run.failed_count,
        failed=run.failed_count,
        duration_seconds=run.duration_seconds,
        top_10=top_10,
        worst_10=worst_10,
        parameter_summary=_build_parameter_summary(run, ranked),
        metric_distributions=_build_metric_distributions(completed_results),
    )


def _build_parameter_summary(
    run: OptimizationRun, ranked: list[RankedOptimizationResult]
) -> tuple[ParameterValueSummary, ...]:
    score_by_experiment_id = {
        ranked_result.result.experiment_result.experiment.experiment_id: ranked_result.score
        for ranked_result in ranked
    }

    summaries: list[ParameterValueSummary] = []
    for parameter in run.parameter_space.parameters:
        scores_by_value: dict[GridValue, list[float]] = {}
        counts_by_value: dict[GridValue, int] = {}

        for result in run.results:
            if result.failed:
                continue
            value = result.parameter_values[parameter.name]
            counts_by_value[value] = counts_by_value.get(value, 0) + 1

            score = score_by_experiment_id.get(result.experiment_result.experiment.experiment_id)
            if score is not None:
                scores_by_value.setdefault(value, []).append(score)

        for value in sorted(counts_by_value):
            scores = scores_by_value.get(value, [])
            summaries.append(
                ParameterValueSummary(
                    parameter_name=parameter.name,
                    value=value,
                    combinations_tested=counts_by_value[value],
                    average_weighted_score=(
                        statistics.fmean(scores) if scores else None
                    ),
                )
            )

    return tuple(summaries)


def _build_metric_distributions(
    completed_results: list[OptimizationResult],
) -> tuple[MetricDistribution, ...]:
    distributions = []
    for metric in Metric:
        values = [
            value
            for value in (
                extract_metric(result.experiment_result, metric) for result in completed_results
            )
            if value is not None
        ]
        if values:
            distributions.append(
                MetricDistribution(
                    metric=metric,
                    minimum=min(values),
                    maximum=max(values),
                    mean=statistics.fmean(values),
                    median=statistics.median(values),
                    sample_size=len(values),
                )
            )
        else:
            distributions.append(
                MetricDistribution(
                    metric=metric,
                    minimum=None,
                    maximum=None,
                    mean=None,
                    median=None,
                    sample_size=0,
                )
            )
    return tuple(distributions)


def render_markdown(report: OptimizationReport) -> str:
    lines = ["# Optimization Report", ""]
    lines.append(f"- Run ID: `{report.run_id}`")
    lines.append(f"- Total combinations: {report.total_combinations}")
    lines.append(f"- Completed: {report.completed}")
    lines.append(f"- Failed: {report.failed}")
    lines.append(f"- Duration: {report.duration_seconds:.3f}s")
    lines.append("")

    lines.append("## Top 10 Configurations")
    lines.append("")
    lines.extend(_ranked_table(report.top_10))
    lines.append("")

    lines.append("## Worst 10 Configurations")
    lines.append("")
    lines.extend(_ranked_table(report.worst_10))
    lines.append("")

    lines.append("## Parameter Summary")
    lines.append("")
    lines.append("| Parameter | Value | Combinations Tested | Avg Weighted Score |")
    lines.append("|---|---|---|---|")
    for summary in report.parameter_summary:
        score = (
            f"{summary.average_weighted_score:.4f}"
            if summary.average_weighted_score is not None
            else "N/A"
        )
        lines.append(
            f"| {summary.parameter_name} | {summary.value} | "
            f"{summary.combinations_tested} | {score} |"
        )
    lines.append("")

    lines.append("## Metric Distributions")
    lines.append("")
    lines.append("| Metric | Min | Max | Mean | Median | Sample Size |")
    lines.append("|---|---|---|---|---|---|")
    for distribution in report.metric_distributions:
        lines.append(
            f"| {distribution.metric.value} | {_fmt(distribution.minimum)} | "
            f"{_fmt(distribution.maximum)} | {_fmt(distribution.mean)} | "
            f"{_fmt(distribution.median)} | {distribution.sample_size} |"
        )
    lines.append("")

    return "\n".join(lines)


def _ranked_table(ranked_results: tuple[RankedOptimizationResult, ...]) -> list[str]:
    lines = ["| Rank | Combination | Parameters | Score |", "|---|---|---|---|"]
    for ranked_result in ranked_results:
        result = ranked_result.result
        params = ", ".join(f"{key}={value}" for key, value in result.parameter_values.items())
        score = f"{ranked_result.score:.4f}" if ranked_result.score is not None else "N/A"
        lines.append(f"| {ranked_result.rank} | {result.combination_id} | {params} | {score} |")
    return lines


def _fmt(value: float | None) -> str:
    return f"{value:.4f}" if value is not None else "N/A"
