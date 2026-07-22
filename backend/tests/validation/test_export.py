import csv
import json
from datetime import datetime

from app.validation.export import export_csv, export_json, export_markdown
from app.validation.models import (
    PassFailAssessment,
    RuleEvaluation,
    ValidationResult,
    ValidationRules,
    ValidationRun,
    Window,
    WindowConfig,
    WindowStatus,
    WindowType,
)
from app.validation.report import build_validation_report
from tests.research.helpers import make_synthetic_result


def _make_run() -> ValidationRun:
    window = Window(
        window_index=0,
        train_start=datetime(2026, 1, 1),
        train_end=datetime(2026, 1, 7),
        test_start=datetime(2026, 1, 7),
        test_end=datetime(2026, 1, 10),
    )
    result = ValidationResult(
        window=window,
        status=WindowStatus.COMPLETED,
        best_parameter_values={"risk_percent": 1.0},
        train_result=make_synthetic_result(name="train", net_profit=1000.0),
        test_result=make_synthetic_result(name="test", net_profit=800.0),
        pass_fail=PassFailAssessment(
            passed=True,
            evaluations=(RuleEvaluation(rule_name="r", passed=True, detail="d"),),
        ),
        error=None,
    )
    return ValidationRun(
        run_id="export-test-run",
        created_date=datetime(2026, 1, 1),
        strategy_name="EMABreakout",
        dataset_path="dummy.csv",
        window_config=WindowConfig(
            window_type=WindowType.ROLLING,
            training_duration_days=6,
            testing_duration_days=3,
            step_size_days=3,
            minimum_candles=10,
            minimum_trades=0,
        ),
        validation_rules=ValidationRules(
            max_drawdown_increase_percent=1000.0,
            min_profit_factor=0.0,
            max_performance_degradation_percent=1000.0,
            min_trade_count=0,
            min_robustness_score_percent=60.0,
        ),
        results=(result,),
        duration_seconds=1.0,
    )


def test_export_json_includes_window_fields_and_params(tmp_path) -> None:  # type: ignore[no-untyped-def]
    report = build_validation_report(_make_run())
    path = tmp_path / "report.json"

    export_json(report, path)

    data = json.loads(path.read_text())
    assert data["run_id"] == "export-test-run"
    row = data["windows"][0]
    assert row["train_net_profit"] == 1000.0
    assert row["test_net_profit"] == 800.0
    assert row["param_risk_percent"] == 1.0
    assert row["passed"] is True


def test_export_csv_produces_a_row_per_window(tmp_path) -> None:  # type: ignore[no-untyped-def]
    report = build_validation_report(_make_run())
    path = tmp_path / "report.csv"

    export_csv(report, path)

    with open(path, newline="") as csv_file:
        rows = list(csv.DictReader(csv_file))

    assert len(rows) == 1
    assert rows[0]["status"] == "Completed"


def test_export_markdown_produces_a_readable_file(tmp_path) -> None:  # type: ignore[no-untyped-def]
    report = build_validation_report(_make_run())
    path = tmp_path / "report.md"

    export_markdown(report, path)

    content = path.read_text()
    assert "# Walk-Forward Validation Report" in content


def test_export_csv_handles_no_windows(tmp_path) -> None:  # type: ignore[no-untyped-def]
    run = _make_run().model_copy(update={"results": ()})
    report = build_validation_report(run)
    path = tmp_path / "empty.csv"

    export_csv(report, path)

    assert path.read_text() == ""
