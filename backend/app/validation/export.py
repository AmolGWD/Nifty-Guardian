"""
Exports a ValidationReport's window-by-window summary to CSV/JSON, and
the full report to Markdown (via `report.render_markdown()`).

Unlike `app.optimization.export` (which unwraps into
`app.research.export`'s existing per-experiment row format), a walk-
forward window's summary is a genuinely different shape - one row
pairs a *train* and a *test* result together with a window's date
range and pass/fail outcome, which no existing exporter represents.
This module only serializes already-computed `WindowSummary`/
`ValidationReport` values (built by `report.py`) - it performs no
metric calculation of its own.
"""

import csv
import json
from pathlib import Path

from app.validation.models import ValidationReport, WindowSummary
from app.validation.report import render_markdown


def _window_summary_row(summary: WindowSummary) -> dict[str, object]:
    row: dict[str, object] = {
        "window_index": summary.window_index,
        "status": summary.status.value,
        "train_start": summary.train_start.isoformat(),
        "train_end": summary.train_end.isoformat(),
        "test_start": summary.test_start.isoformat(),
        "test_end": summary.test_end.isoformat(),
        "train_net_profit": summary.train_net_profit,
        "test_net_profit": summary.test_net_profit,
        "train_win_rate": summary.train_win_rate,
        "test_win_rate": summary.test_win_rate,
        "train_profit_factor": summary.train_profit_factor,
        "test_profit_factor": summary.test_profit_factor,
        "train_max_drawdown": summary.train_max_drawdown,
        "test_max_drawdown": summary.test_max_drawdown,
        "performance_degradation_percent": summary.performance_degradation_percent,
        "passed": summary.passed,
    }
    for key, value in (summary.best_parameter_values or {}).items():
        row[f"param_{key}"] = value
    return row


def export_json(report: ValidationReport, path: str | Path) -> None:
    rows = [_window_summary_row(summary) for summary in report.window_summaries]
    payload = {
        "run_id": report.run_id,
        "robustness_score": report.robustness_score,
        "overall_passed": report.overall_passed,
        "windows": rows,
    }
    Path(path).write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")


def export_csv(report: ValidationReport, path: str | Path) -> None:
    rows = [_window_summary_row(summary) for summary in report.window_summaries]

    if not rows:
        Path(path).write_text("", encoding="utf-8")
        return

    fieldnames = list(rows[0].keys())
    with open(path, "w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def export_markdown(report: ValidationReport, path: str | Path) -> None:
    Path(path).write_text(render_markdown(report), encoding="utf-8")
