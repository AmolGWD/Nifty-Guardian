import csv
import json
from datetime import datetime

from app.monte_carlo.export import export_csv, export_json, export_markdown
from app.monte_carlo.models import MonteCarloRun, PerturbationConfig, SimulationResult
from app.monte_carlo.report import build_report


def _result(index: int, *, return_percent: float) -> SimulationResult:
    return SimulationResult(
        simulation_index=index,
        final_capital=100_000.0 * (1 + return_percent / 100),
        net_profit=100_000.0 * return_percent / 100,
        total_return_percent=return_percent,
        max_drawdown=50.0,
        total_trades=3,
    )


def _make_run(results: list[SimulationResult]) -> MonteCarloRun:
    return MonteCarloRun(
        run_id="export-test-run",
        created_date=datetime(2026, 1, 1),
        seed=1,
        num_simulations=len(results),
        perturbation_config=PerturbationConfig(trade_shuffle_enabled=True),
        initial_capital=100_000.0,
        baseline_net_profit=1000.0,
        baseline_max_drawdown=100.0,
        results=tuple(results),
        duration_seconds=0.5,
    )


def test_export_json_includes_statistics_and_recommendations(tmp_path) -> None:  # type: ignore[no-untyped-def]
    run = _make_run([_result(i, return_percent=float(i)) for i in range(5)])
    report = build_report(run)
    path = tmp_path / "report.json"

    export_json(report, path)

    data = json.loads(path.read_text())
    assert data["run_id"] == "export-test-run"
    assert "statistics" in data
    assert len(data["recommendations"]) > 0


def test_export_csv_produces_one_row_per_unique_simulation(tmp_path) -> None:  # type: ignore[no-untyped-def]
    run = _make_run([_result(i, return_percent=float(i)) for i in range(3)])
    report = build_report(run, top_n=10)
    path = tmp_path / "report.csv"

    export_csv(report, path)

    with open(path, newline="") as csv_file:
        rows = list(csv.DictReader(csv_file))

    assert len(rows) == 3  # only 3 simulations total, worst/best overlap fully - deduplicated


def test_export_markdown_produces_a_readable_file(tmp_path) -> None:  # type: ignore[no-untyped-def]
    run = _make_run([_result(0, return_percent=1.0)])
    report = build_report(run)
    path = tmp_path / "report.md"

    export_markdown(report, path)

    content = path.read_text()
    assert "# Monte Carlo Analysis Report" in content
