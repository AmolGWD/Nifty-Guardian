import json
from pathlib import Path

from app.signals.models import DailyPerformanceReport
from app.signals.report_exporter import export_daily_report_json
from app.trading.strategy.models import StrategyDirection


def _report(**overrides: object) -> DailyPerformanceReport:
    base: dict[str, object] = dict(
        report_date="2026-01-05",
        total_signals=2,
        buy_ce_count=1,
        buy_pe_count=1,
        winning_trades=1,
        losing_trades=1,
        win_rate=50.0,
        net_points=100.0,
        average_pnl=50.0,
        average_reward_risk_ratio=2.0,
        best_trade=None,
        worst_trade=None,
        highest_guardian_score=90.0,
        average_hold_time_seconds=5400.0,
        market_bias=StrategyDirection.NONE,
        guardian_status="Active",
    )
    base.update(overrides)
    return DailyPerformanceReport(**base)


def test_export_creates_the_directory_and_writes_a_named_json_file(tmp_path: Path) -> None:
    directory = tmp_path / "reports"

    path = export_daily_report_json(_report(), directory=directory)

    assert path == directory / "2026-01-05.json"
    assert path.exists()


def test_exported_json_round_trips_the_report_fields(tmp_path: Path) -> None:
    report = _report(total_signals=5, win_rate=80.0)

    path = export_daily_report_json(report, directory=tmp_path)

    written = json.loads(path.read_text())
    assert written["total_signals"] == 5
    assert written["win_rate"] == 80.0
    assert written["report_date"] == "2026-01-05"


def test_export_overwrites_an_existing_file_for_the_same_date(tmp_path: Path) -> None:
    export_daily_report_json(_report(total_signals=1), directory=tmp_path)
    path = export_daily_report_json(_report(total_signals=9), directory=tmp_path)

    written = json.loads(path.read_text())
    assert written["total_signals"] == 9
