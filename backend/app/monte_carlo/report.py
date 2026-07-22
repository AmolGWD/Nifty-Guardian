"""
Builds a MonteCarloReport (summary, risk profile, distribution/
probability statistics, worst/best cases, perturbation summary, and a
few rule-based recommendations) from a completed MonteCarloRun, and
renders it to Markdown.

Recommendations are template strings triggered by fixed, documented
thresholds against the computed statistics (see
docs/MONTE_CARLO_GUIDE.md) - not AI-generated, and never claims more
than the numbers themselves support.
"""

from pydantic import BaseModel, ConfigDict

from app.monte_carlo.models import MonteCarloRun, SimulationResult
from app.monte_carlo.statistics import MonteCarloStatistics, compute_statistics

_TOP_N = 10

# Thresholds behind each recommendation - documented, not hidden.
_HIGH_LOSS_PROBABILITY_PERCENT = 50.0
_DRAWDOWN_INFLATION_MULTIPLIER = 1.5
_WIDE_CONFIDENCE_INTERVAL_SPREAD_PERCENT = 50.0


class MonteCarloReport(BaseModel):
    model_config = ConfigDict(frozen=True)

    run_id: str
    num_simulations: int
    seed: int
    baseline_net_profit: float
    baseline_max_drawdown: float
    perturbations_applied: tuple[str, ...]
    statistics: MonteCarloStatistics
    worst_cases: tuple[SimulationResult, ...]
    best_cases: tuple[SimulationResult, ...]
    recommendations: tuple[str, ...]


def build_report(
    run: MonteCarloRun, *, confidence_level_percent: float = 95.0, top_n: int = _TOP_N
) -> MonteCarloReport:
    statistics = compute_statistics(
        list(run.results), confidence_level_percent=confidence_level_percent
    )
    ordered_by_return = sorted(run.results, key=lambda result: result.total_return_percent)

    return MonteCarloReport(
        run_id=run.run_id,
        num_simulations=run.num_simulations,
        seed=run.seed,
        baseline_net_profit=run.baseline_net_profit,
        baseline_max_drawdown=run.baseline_max_drawdown,
        perturbations_applied=run.perturbation_config.enabled_names(),
        statistics=statistics,
        worst_cases=tuple(ordered_by_return[:top_n]),
        best_cases=tuple(reversed(ordered_by_return[-top_n:])),
        recommendations=_build_recommendations(run, statistics),
    )


def _build_recommendations(
    run: MonteCarloRun, statistics: MonteCarloStatistics
) -> tuple[str, ...]:
    recommendations = []

    if statistics.probability_of_loss_percent > _HIGH_LOSS_PROBABILITY_PERCENT:
        recommendations.append(
            f"More than {_HIGH_LOSS_PROBABILITY_PERCENT:.0f}% of simulations resulted in a "
            f"loss ({statistics.probability_of_loss_percent:.1f}%) - the strategy's edge may "
            "not survive the modeled execution uncertainty."
        )

    if (
        run.baseline_max_drawdown > 0
        and statistics.worst_drawdown > run.baseline_max_drawdown * _DRAWDOWN_INFLATION_MULTIPLIER
    ):
        recommendations.append(
            f"Worst simulated drawdown ({statistics.worst_drawdown:.2f}) is more than "
            f"{_DRAWDOWN_INFLATION_MULTIPLIER:.1f}x the original backtest's drawdown "
            f"({run.baseline_max_drawdown:.2f}) - consider more conservative position sizing."
        )

    interval_spread = (
        statistics.confidence_interval.upper_bound - statistics.confidence_interval.lower_bound
    )
    if interval_spread > _WIDE_CONFIDENCE_INTERVAL_SPREAD_PERCENT:
        recommendations.append(
            f"The {statistics.confidence_interval.confidence_level_percent:.0f}% confidence "
            f"interval spans {interval_spread:.1f} percentage points - outcomes are highly "
            "sensitive to the modeled execution uncertainty; treat any single backtest result "
            "as one sample from a wide range, not a forecast."
        )

    recommendations.append(
        "These are statistical observations from perturbed historical trades, not a guarantee "
        "about future performance - see docs/MONTE_CARLO_GUIDE.md's Limitations section."
    )

    return tuple(recommendations)


def render_markdown(report: MonteCarloReport) -> str:
    lines = ["# Monte Carlo Analysis Report", "", "## Summary", ""]
    lines.append(f"- Run ID: `{report.run_id}`")
    lines.append(f"- Simulations: {report.num_simulations}")
    lines.append(f"- Seed: {report.seed}")
    lines.append(f"- Baseline net profit: {report.baseline_net_profit:.4f}")
    lines.append(f"- Baseline max drawdown: {report.baseline_max_drawdown:.4f}")
    lines.append("")

    lines.append("## Perturbation Summary")
    lines.append("")
    lines.append(
        ", ".join(report.perturbations_applied) if report.perturbations_applied else "(none)"
    )
    lines.append("")

    stats = report.statistics
    lines.append("## Distribution Statistics")
    lines.append("")
    lines.append(f"- Mean return: {stats.mean_return_percent:.4f}%")
    lines.append(f"- Median return: {stats.median_return_percent:.4f}%")
    lines.append(f"- Std deviation: {stats.std_dev_return_percent:.4f}%")
    lines.append(f"- Worst return: {stats.worst_return_percent:.4f}%")
    lines.append(f"- Best return: {stats.best_return_percent:.4f}%")
    lines.append(f"- Worst drawdown: {stats.worst_drawdown:.4f}")
    lines.append(f"- Median drawdown: {stats.median_drawdown:.4f}")
    lines.append(
        f"- {stats.confidence_interval.confidence_level_percent:.0f}% confidence interval: "
        f"[{stats.confidence_interval.lower_bound:.4f}%, "
        f"{stats.confidence_interval.upper_bound:.4f}%]"
    )
    lines.append("")

    lines.append("## Risk Profile")
    lines.append("")
    lines.append(f"- Value at Risk (VaR): {stats.value_at_risk_percent:.4f}%")
    lines.append(f"- Conditional VaR (CVaR): {stats.conditional_value_at_risk_percent:.4f}%")
    lines.append("")

    lines.append("## Probability Metrics")
    lines.append("")
    lines.append(f"- Probability of profit: {stats.probability_of_profit_percent:.2f}%")
    lines.append(f"- Probability of loss: {stats.probability_of_loss_percent:.2f}%")
    lines.append("")

    lines.append("## Worst Cases")
    lines.append("")
    lines.extend(_simulation_table(report.worst_cases))
    lines.append("")

    lines.append("## Best Cases")
    lines.append("")
    lines.extend(_simulation_table(report.best_cases))
    lines.append("")

    lines.append("## Recommendations")
    lines.append("")
    for recommendation in report.recommendations:
        lines.append(f"- {recommendation}")
    lines.append("")

    return "\n".join(lines)


def _simulation_table(results: tuple[SimulationResult, ...]) -> list[str]:
    lines = ["| Simulation | Return % | Max Drawdown | Trades |", "|---|---|---|---|"]
    for result in results:
        lines.append(
            f"| {result.simulation_index} | {result.total_return_percent:.4f}% | "
            f"{result.max_drawdown:.4f} | {result.total_trades} |"
        )
    return lines
