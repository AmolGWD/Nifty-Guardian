"""
Writes a `DailyPerformanceReport` to disk as JSON - the brief's "End
of Day Report... Export JSON" requirement. One file per trading day
(`<directory>/<report_date>.json`), overwritten if called again for
the same date (e.g. an on-demand export before the day has actually
ended) rather than accumulating duplicates.
"""

from pathlib import Path

from app.signals.models import DailyPerformanceReport

DEFAULT_REPORTS_DIRECTORY = Path(__file__).resolve().parents[2] / "data" / "reports"


def export_daily_report_json(
    report: DailyPerformanceReport, *, directory: Path = DEFAULT_REPORTS_DIRECTORY
) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{report.report_date}.json"
    path.write_text(report.model_dump_json(indent=2))
    return path
