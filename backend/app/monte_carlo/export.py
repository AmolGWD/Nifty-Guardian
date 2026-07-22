"""
Exports a MonteCarloReport's per-simulation results to CSV/JSON, and
the full report to Markdown (via `report.render_markdown()`). Only
serializes already-computed values - no statistic is calculated here.
"""

import csv
import json
from pathlib import Path

from app.monte_carlo.models import SimulationResult
from app.monte_carlo.report import MonteCarloReport, render_markdown


def _simulation_row(result: SimulationResult) -> dict[str, object]:
    return {
        "simulation_index": result.simulation_index,
        "final_capital": result.final_capital,
        "net_profit": result.net_profit,
        "total_return_percent": result.total_return_percent,
        "max_drawdown": result.max_drawdown,
        "total_trades": result.total_trades,
    }


def export_json(report: MonteCarloReport, path: str | Path) -> None:
    payload = {
        "run_id": report.run_id,
        "num_simulations": report.num_simulations,
        "seed": report.seed,
        "perturbations_applied": list(report.perturbations_applied),
        "statistics": report.statistics.model_dump(mode="json"),
        "recommendations": list(report.recommendations),
        "worst_cases": [_simulation_row(result) for result in report.worst_cases],
        "best_cases": [_simulation_row(result) for result in report.best_cases],
    }
    Path(path).write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")


def export_csv(report: MonteCarloReport, path: str | Path) -> None:
    seen_indices: set[int] = set()
    unique_results = []
    for result in report.best_cases + report.worst_cases:
        if result.simulation_index not in seen_indices:
            seen_indices.add(result.simulation_index)
            unique_results.append(result)
    rows = [_simulation_row(result) for result in unique_results]

    if not rows:
        Path(path).write_text("", encoding="utf-8")
        return

    fieldnames = list(rows[0].keys())
    with open(path, "w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def export_markdown(report: MonteCarloReport, path: str | Path) -> None:
    Path(path).write_text(render_markdown(report), encoding="utf-8")
