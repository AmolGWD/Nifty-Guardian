from datetime import datetime

from app.monte_carlo.models import MonteCarloRun, PerturbationConfig, SimulationResult
from app.monte_carlo.perturbations.slippage import SlippageConfig
from app.monte_carlo.report import build_report, render_markdown


def _result(index: int, *, return_percent: float, drawdown: float = 0.0) -> SimulationResult:
    return SimulationResult(
        simulation_index=index,
        final_capital=100_000.0 * (1 + return_percent / 100),
        net_profit=100_000.0 * return_percent / 100,
        total_return_percent=return_percent,
        max_drawdown=drawdown,
        total_trades=5,
    )


def _make_run(
    results: list[SimulationResult], *, baseline_max_drawdown: float = 100.0
) -> MonteCarloRun:
    return MonteCarloRun(
        run_id="test-run",
        created_date=datetime(2026, 1, 1),
        seed=1,
        num_simulations=len(results),
        perturbation_config=PerturbationConfig(
            trade_shuffle_enabled=True,
            slippage=SlippageConfig(entry_slippage_percent=0.1, exit_slippage_percent=0.1),
        ),
        initial_capital=100_000.0,
        baseline_net_profit=1000.0,
        baseline_max_drawdown=baseline_max_drawdown,
        results=tuple(results),
        duration_seconds=0.5,
    )


def test_report_includes_perturbation_names() -> None:
    run = _make_run([_result(0, return_percent=1.0)])

    report = build_report(run)

    assert "TradeShuffle" in report.perturbations_applied
    assert "Slippage" in report.perturbations_applied


def test_worst_and_best_cases_are_ordered_correctly() -> None:
    run = _make_run(
        [_result(i, return_percent=value) for i, value in enumerate([5.0, -10.0, 2.0, -3.0, 8.0])]
    )

    report = build_report(run, top_n=2)

    assert [r.total_return_percent for r in report.worst_cases] == [-10.0, -3.0]
    assert [r.total_return_percent for r in report.best_cases] == [8.0, 5.0]


def test_high_loss_probability_triggers_a_recommendation() -> None:
    run = _make_run(
        [_result(i, return_percent=value) for i, value in enumerate([-5.0, -3.0, -2.0, 1.0])]
    )

    report = build_report(run)

    assert any("loss" in recommendation.lower() for recommendation in report.recommendations)


def test_drawdown_inflation_triggers_a_recommendation() -> None:
    run = _make_run(
        [_result(0, return_percent=1.0, drawdown=500.0)], baseline_max_drawdown=100.0
    )

    report = build_report(run)

    assert any("drawdown" in recommendation.lower() for recommendation in report.recommendations)


def test_always_includes_the_limitations_disclaimer() -> None:
    run = _make_run([_result(0, return_percent=1.0)])

    report = build_report(run)

    assert any("not a guarantee" in r.lower() for r in report.recommendations)


def test_render_markdown_contains_expected_sections() -> None:
    run = _make_run([_result(0, return_percent=1.0)])

    report = build_report(run)
    markdown = render_markdown(report)

    assert "# Monte Carlo Analysis Report" in markdown
    assert "## Summary" in markdown
    assert "## Risk Profile" in markdown
    assert "## Distribution Statistics" in markdown
    assert "## Probability Metrics" in markdown
    assert "## Worst Cases" in markdown
    assert "## Best Cases" in markdown
    assert "## Perturbation Summary" in markdown
    assert "## Recommendations" in markdown
