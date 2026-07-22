"""
Builds a ValidationReport (robustness score, train/test comparison,
per-window summary, parameter stability, pass/fail assessment) from a
completed ValidationRun, and renders it to Markdown.

Only COMPLETED windows contribute to every aggregate statistic here
(robustness score, stability summaries, parameter stability) -
INSUFFICIENT_DATA and FAILED windows are still counted and reported
separately (see `ValidationReport.insufficient_data_windows`/
`failed_windows`), but averaging a metric across a window that never
produced one would be meaningless, not conservative.
"""

import statistics
from collections import Counter
from collections.abc import Callable

from app.optimization.models import GridValue
from app.trading.analytics.models import OverallPerformance
from app.validation.models import (
    MetricStabilitySummary,
    ParameterStability,
    ValidationReport,
    ValidationResult,
    ValidationRun,
    WindowStatus,
    WindowSummary,
)
from app.validation.validator import compute_performance_degradation

_TOP_N = 10


def build_validation_report(run: ValidationRun) -> ValidationReport:
    completed = [result for result in run.results if result.status == WindowStatus.COMPLETED]
    insufficient = [
        result for result in run.results if result.status == WindowStatus.INSUFFICIENT_DATA
    ]
    failed = [result for result in run.results if result.status == WindowStatus.FAILED]
    passed = [
        result for result in completed if result.pass_fail is not None and result.pass_fail.passed
    ]

    robustness_score = 100.0 * len(passed) / len(completed) if completed else 0.0
    overall_passed = (
        len(completed) > 0 and robustness_score >= run.validation_rules.min_robustness_score_percent
    )

    degradations = [
        degradation
        for degradation in (_degradation_for(result) for result in completed)
        if degradation is not None
    ]

    return ValidationReport(
        run_id=run.run_id,
        total_windows=len(run.results),
        completed_windows=len(completed),
        insufficient_data_windows=len(insufficient),
        failed_windows=len(failed),
        passed_windows=len(passed),
        robustness_score=robustness_score,
        overall_passed=overall_passed,
        window_summaries=tuple(_build_window_summary(result) for result in run.results),
        parameter_stability=_build_parameter_stability(completed),
        average_performance_degradation_percent=(
            statistics.fmean(degradations) if degradations else None
        ),
        performance_degradation=_stability_summary(
            "NetProfit", completed, lambda overall: overall.net_profit
        ),
        drawdown_comparison=_stability_summary(
            "MaxDrawdown", completed, lambda overall: overall.max_drawdown
        ),
        equity_comparison=_stability_summary(
            "FinalCapital", completed, lambda overall: overall.final_capital
        ),
        win_rate_stability=_stability_summary(
            "WinRate", completed, lambda overall: overall.win_rate
        ),
        profit_factor_stability=_stability_summary(
            "ProfitFactor", completed, lambda overall: overall.profit_factor
        ),
    )


def _degradation_for(result: ValidationResult) -> float | None:
    train, test = _overall_pair(result)
    if train is None or test is None:
        return None
    return compute_performance_degradation(train, test)


def _overall_pair(
    result: ValidationResult,
) -> tuple[OverallPerformance | None, OverallPerformance | None]:
    train_report = result.train_result.analytics_report if result.train_result else None
    test_report = result.test_result.analytics_report if result.test_result else None
    train = train_report.overall if train_report else None
    test = test_report.overall if test_report else None
    return train, test


def _build_window_summary(result: ValidationResult) -> WindowSummary:
    train, test = _overall_pair(result)

    return WindowSummary(
        window_index=result.window.window_index,
        status=result.status,
        train_start=result.window.train_start,
        train_end=result.window.train_end,
        test_start=result.window.test_start,
        test_end=result.window.test_end,
        best_parameter_values=result.best_parameter_values,
        train_net_profit=train.net_profit if train else None,
        test_net_profit=test.net_profit if test else None,
        train_win_rate=train.win_rate if train else None,
        test_win_rate=test.win_rate if test else None,
        train_profit_factor=train.profit_factor if train else None,
        test_profit_factor=test.profit_factor if test else None,
        train_max_drawdown=train.max_drawdown if train else None,
        test_max_drawdown=test.max_drawdown if test else None,
        performance_degradation_percent=(
            compute_performance_degradation(train, test) if train and test else None
        ),
        passed=result.pass_fail.passed if result.pass_fail else None,
    )


def _build_parameter_stability(
    completed: list[ValidationResult],
) -> tuple[ParameterStability, ...]:
    values_by_parameter: dict[str, list[GridValue]] = {}
    for result in completed:
        if result.best_parameter_values is None:
            continue
        for name, value in result.best_parameter_values.items():
            values_by_parameter.setdefault(name, []).append(value)

    summaries = []
    for name, values in values_by_parameter.items():
        counts = Counter(values)
        most_common_value, most_common_count = (
            counts.most_common(1)[0] if counts else (None, 0)
        )
        summaries.append(
            ParameterStability(
                parameter_name=name,
                values_chosen=tuple(values),
                distinct_value_count=len(counts),
                most_common_value=most_common_value,
                most_common_value_frequency=(
                    most_common_count / len(values) if values else None
                ),
            )
        )
    return tuple(summaries)


def _stability_summary(
    metric_name: str,
    completed: list[ValidationResult],
    extractor: Callable[[OverallPerformance], float | None],
) -> MetricStabilitySummary:
    train_values = []
    test_values = []
    for result in completed:
        train, test = _overall_pair(result)
        if train is None or test is None:
            continue
        train_value = extractor(train)
        test_value = extractor(test)
        if train_value is None or test_value is None:
            continue
        train_values.append(train_value)
        test_values.append(test_value)

    return MetricStabilitySummary(
        metric_name=metric_name,
        train_values=tuple(train_values),
        test_values=tuple(test_values),
        train_mean=statistics.fmean(train_values) if train_values else None,
        test_mean=statistics.fmean(test_values) if test_values else None,
    )


def render_markdown(report: ValidationReport) -> str:
    lines = ["# Walk-Forward Validation Report", ""]
    lines.append(f"- Run ID: `{report.run_id}`")
    lines.append(f"- Total windows: {report.total_windows}")
    lines.append(f"- Completed: {report.completed_windows}")
    lines.append(f"- Insufficient data: {report.insufficient_data_windows}")
    lines.append(f"- Failed: {report.failed_windows}")
    lines.append(f"- Passed: {report.passed_windows}")
    lines.append(f"- **Robustness score: {report.robustness_score:.2f}%**")
    lines.append(f"- **Overall assessment: {'PASS' if report.overall_passed else 'FAIL'}**")
    if report.average_performance_degradation_percent is not None:
        lines.append(
            f"- Average performance degradation: "
            f"{report.average_performance_degradation_percent:.2f}%"
        )
    lines.append("")

    lines.append("## Window-by-Window Summary")
    lines.append("")
    lines.append(
        "| # | Status | Train Net Profit | Test Net Profit | Degradation | "
        "Train Win% | Test Win% | Pass |"
    )
    lines.append("|---|---|---|---|---|---|---|---|")
    for summary in report.window_summaries:
        lines.append(
            f"| {summary.window_index} | {summary.status.value} | "
            f"{_fmt(summary.train_net_profit)} | {_fmt(summary.test_net_profit)} | "
            f"{_fmt(summary.performance_degradation_percent)}% | "
            f"{_fmt(summary.train_win_rate)} | {_fmt(summary.test_win_rate)} | "
            f"{summary.passed if summary.passed is not None else 'N/A'} |"
        )
    lines.append("")

    lines.append("## Train/Test Comparison")
    lines.append("")
    for stability in (
        report.performance_degradation,
        report.drawdown_comparison,
        report.equity_comparison,
        report.win_rate_stability,
        report.profit_factor_stability,
    ):
        lines.append(
            f"- **{stability.metric_name}**: train mean={_fmt(stability.train_mean)}, "
            f"test mean={_fmt(stability.test_mean)} (n={len(stability.train_values)})"
        )
    lines.append("")

    lines.append("## Parameter Stability")
    lines.append("")
    lines.append("| Parameter | Distinct Values | Most Common | Frequency |")
    lines.append("|---|---|---|---|")
    for parameter_stability in report.parameter_stability:
        frequency = (
            f"{parameter_stability.most_common_value_frequency * 100:.1f}%"
            if parameter_stability.most_common_value_frequency is not None
            else "N/A"
        )
        lines.append(
            f"| {parameter_stability.parameter_name} | "
            f"{parameter_stability.distinct_value_count} | "
            f"{parameter_stability.most_common_value} | {frequency} |"
        )
    lines.append("")

    return "\n".join(lines)


def _fmt(value: float | None) -> str:
    return f"{value:.4f}" if value is not None else "N/A"
