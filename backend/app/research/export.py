"""
Exports experiment summaries (experiment metadata, its parameter set,
key performance metrics, and rank position if a ranking is supplied)
to Markdown, CSV, or JSON. All three read from the same
`_build_summary()` so the fields present never drift between formats.
"""

import csv
import json
from pathlib import Path

from app.research.models import ExperimentResult, Metric, extract_metric

_SUMMARY_METRICS = (
    Metric.NET_PROFIT,
    Metric.PROFIT_FACTOR,
    Metric.EXPECTANCY,
    Metric.MAX_DRAWDOWN,
    Metric.RECOVERY_FACTOR,
    Metric.SHARPE_RATIO,
    Metric.CALMAR_RATIO,
    Metric.WIN_RATE,
)


def _build_summary(
    result: ExperimentResult, rank: int | None
) -> dict[str, object]:
    experiment = result.experiment
    summary: dict[str, object] = {
        "experiment_id": experiment.experiment_id,
        "name": experiment.name,
        "description": experiment.description,
        "created_date": experiment.created_date.isoformat(),
        "strategy": experiment.strategy,
        "dataset_path": experiment.dataset_path,
        "timeframe": experiment.timeframe.value,
        "tags": ", ".join(experiment.tags),
        "notes": experiment.notes,
        "git_commit_hash": experiment.git_commit_hash or "",
        "status": result.status.value,
        "duration_seconds": result.duration_seconds,
        "error": result.error or "",
        "rank": rank if rank is not None else "",
    }

    for key, value in experiment.parameters.items():
        summary[f"param_{key}"] = value

    for metric in _SUMMARY_METRICS:
        summary[metric.value] = extract_metric(result, metric)

    return summary


def _rank_lookup(ranking: list[ExperimentResult] | None) -> dict[str, int]:
    if ranking is None:
        return {}
    return {result.experiment.experiment_id: index + 1 for index, result in enumerate(ranking)}


def export_json(
    results: list[ExperimentResult],
    path: str | Path,
    *,
    ranking: list[ExperimentResult] | None = None,
) -> None:
    ranks = _rank_lookup(ranking)
    summaries = [
        _build_summary(result, ranks.get(result.experiment.experiment_id)) for result in results
    ]
    Path(path).write_text(json.dumps(summaries, indent=2, default=str), encoding="utf-8")


def export_csv(
    results: list[ExperimentResult],
    path: str | Path,
    *,
    ranking: list[ExperimentResult] | None = None,
) -> None:
    ranks = _rank_lookup(ranking)
    summaries = [
        _build_summary(result, ranks.get(result.experiment.experiment_id)) for result in results
    ]

    if not summaries:
        Path(path).write_text("", encoding="utf-8")
        return

    fieldnames = list(summaries[0].keys())
    with open(path, "w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(summaries)


def export_markdown(
    results: list[ExperimentResult],
    path: str | Path,
    *,
    ranking: list[ExperimentResult] | None = None,
) -> None:
    ranks = _rank_lookup(ranking)
    ordered = ranking if ranking is not None else results

    lines = ["# Experiment Summary", ""]
    lines.append(
        "| Rank | Name | Strategy | Net Profit | Profit Factor | Win Rate | Max Drawdown | Sharpe |"
    )
    lines.append("|---|---|---|---|---|---|---|---|")

    for result in ordered:
        rank = ranks.get(result.experiment.experiment_id, "")
        net_profit = extract_metric(result, Metric.NET_PROFIT)
        profit_factor = extract_metric(result, Metric.PROFIT_FACTOR)
        win_rate = extract_metric(result, Metric.WIN_RATE)
        max_drawdown = extract_metric(result, Metric.MAX_DRAWDOWN)
        sharpe = extract_metric(result, Metric.SHARPE_RATIO)
        lines.append(
            f"| {rank} | {result.experiment.name} | {result.experiment.strategy} | "
            f"{_fmt(net_profit)} | {_fmt(profit_factor)} | {_fmt(win_rate)}% | "
            f"{_fmt(max_drawdown)} | {_fmt(sharpe)} |"
        )

    lines.append("")
    lines.append("## Details")
    lines.append("")

    for result in ordered:
        experiment = result.experiment
        lines.append(f"### {experiment.name}")
        lines.append("")
        lines.append(f"- Experiment ID: `{experiment.experiment_id}`")
        lines.append(f"- Description: {experiment.description}")
        lines.append(f"- Strategy: {experiment.strategy}")
        lines.append(f"- Dataset: `{experiment.dataset_path}`")
        lines.append(f"- Timeframe: {experiment.timeframe.value}")
        lines.append(f"- Status: {result.status.value}")
        lines.append(
            f"- Duration: {result.duration_seconds:.3f}s"
            if result.duration_seconds is not None
            else "- Duration: N/A"
        )
        lines.append(f"- Tags: {', '.join(experiment.tags) if experiment.tags else '(none)'}")
        lines.append(f"- Notes: {experiment.notes or '(none)'}")
        lines.append(f"- Git commit: {experiment.git_commit_hash or 'N/A'}")
        if result.error:
            lines.append(f"- Error: {result.error}")

        lines.append("")
        lines.append("**Parameters**")
        lines.append("")
        if experiment.parameters:
            for key, value in experiment.parameters.items():
                lines.append(f"- {key}: {value}")
        else:
            lines.append("(none)")

        lines.append("")
        lines.append("**Performance Metrics**")
        lines.append("")
        for metric in _SUMMARY_METRICS:
            lines.append(f"- {metric.value}: {_fmt(extract_metric(result, metric))}")
        lines.append("")

    Path(path).write_text("\n".join(lines), encoding="utf-8")


def _fmt(value: float | None) -> str:
    return f"{value:.4f}" if value is not None else "N/A"
