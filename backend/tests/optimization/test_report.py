from datetime import datetime

from app.optimization.models import OptimizationResult, OptimizationRun
from app.optimization.parameter_space import EMA_PERIOD, ParameterSpace
from app.optimization.ranking import RankBy
from app.optimization.report import build_optimization_report, render_markdown
from tests.optimization.helpers import make_optimization_result


def _make_run(results: list[OptimizationResult]) -> OptimizationRun:
    return OptimizationRun(
        run_id="test-run",
        created_date=datetime(2026, 7, 21, 12, 0),
        strategy_name="EMABreakout",
        dataset_path="dummy.csv",
        parameter_space=ParameterSpace(parameters=(EMA_PERIOD,)),
        results=tuple(results),
        total_combinations=len(results),
        failed_count=sum(1 for r in results if r.failed),
        duration_seconds=1.234,
    )


def test_report_statistics_match_the_run() -> None:
    results = [
        make_optimization_result(
            combination_id=f"c{i}", parameter_values={"ema_period": 10 + 2 * i}
        )
        for i in range(3)
    ]
    results.append(
        make_optimization_result(
            combination_id="failed", parameter_values={"ema_period": 20}, failed=True
        )
    )
    run = _make_run(results)

    report = build_optimization_report(run)

    assert report.run_id == "test-run"
    assert report.total_combinations == 4
    assert report.completed == 3
    assert report.failed == 1
    assert report.duration_seconds == 1.234


def test_top_10_excludes_failed_results() -> None:
    results = [
        make_optimization_result(combination_id="ok", net_profit=100.0),
        make_optimization_result(combination_id="failed", failed=True),
    ]
    run = _make_run(results)

    report = build_optimization_report(run)

    assert len(report.top_10) == 1
    assert report.top_10[0].result.combination_id == "ok"


def test_top_10_is_capped_at_ten() -> None:
    results = [
        make_optimization_result(combination_id=f"c{i}", net_profit=float(i)) for i in range(15)
    ]
    run = _make_run(results)

    report = build_optimization_report(run, rank_by=RankBy.NET_PROFIT)

    assert len(report.top_10) == 10
    assert report.top_10[0].result.combination_id == "c14"


def test_worst_10_is_ordered_worst_first() -> None:
    results = [
        make_optimization_result(combination_id=f"c{i}", net_profit=float(i)) for i in range(15)
    ]
    run = _make_run(results)

    report = build_optimization_report(run, rank_by=RankBy.NET_PROFIT)

    assert len(report.worst_10) == 10
    assert report.worst_10[0].result.combination_id == "c0"


def test_parameter_summary_groups_by_distinct_value() -> None:
    results = [
        make_optimization_result(
            combination_id="a", parameter_values={"ema_period": 14}, net_profit=100.0
        ),
        make_optimization_result(
            combination_id="b", parameter_values={"ema_period": 14}, net_profit=200.0
        ),
        make_optimization_result(
            combination_id="c", parameter_values={"ema_period": 20}, net_profit=300.0
        ),
    ]
    run = _make_run(results)

    report = build_optimization_report(run, rank_by=RankBy.NET_PROFIT)

    by_value = {s.value: s for s in report.parameter_summary}
    assert by_value[14].combinations_tested == 2
    assert by_value[20].combinations_tested == 1


def test_metric_distributions_present_for_completed_results() -> None:
    results = [
        make_optimization_result(combination_id="a", net_profit=100.0),
        make_optimization_result(combination_id="b", net_profit=300.0),
    ]
    run = _make_run(results)

    report = build_optimization_report(run)

    from app.research.models import Metric

    net_profit_distribution = next(
        d for d in report.metric_distributions if d.metric == Metric.NET_PROFIT
    )
    assert net_profit_distribution.minimum == 100.0
    assert net_profit_distribution.maximum == 300.0
    assert net_profit_distribution.mean == 200.0
    assert net_profit_distribution.sample_size == 2


def test_metric_distribution_is_empty_when_every_result_failed() -> None:
    run = _make_run([make_optimization_result(combination_id="failed", failed=True)])

    report = build_optimization_report(run)

    assert all(d.sample_size == 0 for d in report.metric_distributions)
    assert all(d.minimum is None for d in report.metric_distributions)


def test_render_markdown_contains_expected_sections() -> None:
    run = _make_run([make_optimization_result(combination_id="a")])

    report = build_optimization_report(run)
    markdown = render_markdown(report)

    assert "# Optimization Report" in markdown
    assert "## Top 10 Configurations" in markdown
    assert "## Worst 10 Configurations" in markdown
    assert "## Parameter Summary" in markdown
    assert "## Metric Distributions" in markdown
    assert "test-run" in markdown
