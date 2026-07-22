from datetime import datetime

import pytest

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
from app.validation.report import build_validation_report, render_markdown
from tests.research.helpers import make_synthetic_result


def _window(index: int = 0) -> Window:
    return Window(
        window_index=index,
        train_start=datetime(2026, 1, 1),
        train_end=datetime(2026, 1, 7),
        test_start=datetime(2026, 1, 7),
        test_end=datetime(2026, 1, 10),
    )


def _completed_result(
    *,
    index: int = 0,
    train_net_profit: float = 1000.0,
    test_net_profit: float = 800.0,
    passed: bool = True,
    parameter_values: dict[str, float] | None = None,
) -> ValidationResult:
    train_result = make_synthetic_result(name=f"train-{index}", net_profit=train_net_profit)
    test_result = make_synthetic_result(name=f"test-{index}", net_profit=test_net_profit)

    return ValidationResult(
        window=_window(index),
        status=WindowStatus.COMPLETED,
        best_parameter_values=parameter_values or {"risk_percent": 1.0},
        train_result=train_result,
        test_result=test_result,
        pass_fail=PassFailAssessment(
            passed=passed,
            evaluations=(RuleEvaluation(rule_name="test_rule", passed=passed, detail="test"),),
        ),
        error=None,
    )


def _insufficient_result(index: int = 0) -> ValidationResult:
    return ValidationResult(
        window=_window(index),
        status=WindowStatus.INSUFFICIENT_DATA,
        best_parameter_values=None,
        train_result=None,
        test_result=None,
        pass_fail=None,
        error="not enough data",
    )


def _make_run(results: list[ValidationResult], **rule_overrides: object) -> ValidationRun:
    rules: dict[str, object] = dict(
        max_drawdown_increase_percent=1000.0,
        min_profit_factor=0.0,
        max_performance_degradation_percent=1000.0,
        min_trade_count=0,
        min_robustness_score_percent=60.0,
    )
    rules.update(rule_overrides)

    return ValidationRun(
        run_id="test-run",
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
        validation_rules=ValidationRules(**rules),
        results=tuple(results),
        duration_seconds=1.5,
    )


def test_report_counts_match_the_run() -> None:
    run = _make_run(
        [
            _completed_result(index=0, passed=True),
            _completed_result(index=1, passed=False),
            _insufficient_result(index=2),
        ]
    )

    report = build_validation_report(run)

    assert report.total_windows == 3
    assert report.completed_windows == 2
    assert report.insufficient_data_windows == 1
    assert report.failed_windows == 0
    assert report.passed_windows == 1


def test_robustness_score_is_percent_of_completed_windows_passed() -> None:
    run = _make_run(
        [
            _completed_result(index=0, passed=True),
            _completed_result(index=1, passed=True),
            _completed_result(index=2, passed=False),
        ]
    )

    report = build_validation_report(run)

    assert report.robustness_score == pytest.approx((2 / 3) * 100)


def test_robustness_score_is_zero_when_no_windows_completed() -> None:
    run = _make_run([_insufficient_result(index=0)])

    report = build_validation_report(run)

    assert report.robustness_score == 0.0
    assert report.overall_passed is False


def test_overall_passed_respects_configured_threshold() -> None:
    results = [_completed_result(index=i, passed=(i < 3)) for i in range(4)]  # 75% pass

    strict_run = _make_run(results, min_robustness_score_percent=80.0)
    lenient_run = _make_run(results, min_robustness_score_percent=50.0)

    assert build_validation_report(strict_run).overall_passed is False
    assert build_validation_report(lenient_run).overall_passed is True


def test_window_summaries_include_insufficient_data_windows() -> None:
    run = _make_run([_completed_result(index=0), _insufficient_result(index=1)])

    report = build_validation_report(run)

    assert len(report.window_summaries) == 2
    assert report.window_summaries[1].status == WindowStatus.INSUFFICIENT_DATA
    assert report.window_summaries[1].train_net_profit is None


def test_parameter_stability_tracks_chosen_values() -> None:
    run = _make_run(
        [
            _completed_result(index=0, parameter_values={"risk_percent": 1.0}),
            _completed_result(index=1, parameter_values={"risk_percent": 1.0}),
            _completed_result(index=2, parameter_values={"risk_percent": 0.5}),
        ]
    )

    report = build_validation_report(run)

    stability = next(s for s in report.parameter_stability if s.parameter_name == "risk_percent")
    assert stability.distinct_value_count == 2
    assert stability.most_common_value == 1.0
    assert stability.most_common_value_frequency == 2 / 3


def test_performance_degradation_stability_summary() -> None:
    run = _make_run(
        [
            _completed_result(index=0, train_net_profit=1000.0, test_net_profit=800.0),
            _completed_result(index=1, train_net_profit=1000.0, test_net_profit=600.0),
        ]
    )

    report = build_validation_report(run)

    assert report.performance_degradation.train_mean == 1000.0
    assert report.performance_degradation.test_mean == 700.0
    assert report.average_performance_degradation_percent == 30.0


def test_render_markdown_contains_expected_sections() -> None:
    run = _make_run([_completed_result(index=0)])

    report = build_validation_report(run)
    markdown = render_markdown(report)

    assert "# Walk-Forward Validation Report" in markdown
    assert "## Window-by-Window Summary" in markdown
    assert "## Train/Test Comparison" in markdown
    assert "## Parameter Stability" in markdown
    assert "Robustness score" in markdown
