"""
Cross-simulation statistics: distribution, risk, and probability
metrics computed over a completed Monte Carlo run's results. This is
genuinely new arithmetic this phase adds (no existing package computes
VaR/CVaR/confidence intervals over many simulated outcomes) - not a
duplicate of anything `app.trading.analytics`/`app.trading.backtest`
already does, which only ever analyze a single backtest run.

VaR/CVaR convention (see docs/MONTE_CARLO_GUIDE.md for the full
explanation): both are expressed as positive loss magnitudes at the
configured confidence level, computed non-parametrically from the
simulated return distribution's own tail - no assumption that returns
are normally distributed, appropriate for a Monte Carlo sample.
"""

import statistics as stats

from pydantic import BaseModel, ConfigDict

from app.monte_carlo.models import SimulationResult


class ConfidenceInterval(BaseModel):
    model_config = ConfigDict(frozen=True)

    confidence_level_percent: float
    lower_bound: float
    upper_bound: float


class MonteCarloStatistics(BaseModel):
    model_config = ConfigDict(frozen=True)

    sample_size: int
    mean_return_percent: float
    median_return_percent: float
    std_dev_return_percent: float
    worst_return_percent: float
    best_return_percent: float
    worst_drawdown: float
    median_drawdown: float
    confidence_interval: ConfidenceInterval
    probability_of_profit_percent: float
    probability_of_loss_percent: float
    value_at_risk_percent: float
    conditional_value_at_risk_percent: float


def compute_statistics(
    results: list[SimulationResult], *, confidence_level_percent: float = 95.0
) -> MonteCarloStatistics:
    if not results:
        raise ValueError("compute_statistics requires at least one simulation result")

    returns = sorted(result.total_return_percent for result in results)
    drawdowns = sorted(result.max_drawdown for result in results)

    profitable = sum(1 for value in returns if value > 0)
    unprofitable = sum(1 for value in returns if value < 0)

    return MonteCarloStatistics(
        sample_size=len(results),
        mean_return_percent=stats.fmean(returns),
        median_return_percent=stats.median(returns),
        std_dev_return_percent=stats.pstdev(returns) if len(returns) > 1 else 0.0,
        worst_return_percent=returns[0],
        best_return_percent=returns[-1],
        worst_drawdown=drawdowns[-1],
        median_drawdown=stats.median(drawdowns),
        confidence_interval=_confidence_interval(returns, confidence_level_percent),
        probability_of_profit_percent=profitable / len(returns) * 100,
        probability_of_loss_percent=unprofitable / len(returns) * 100,
        value_at_risk_percent=_value_at_risk(returns, confidence_level_percent),
        conditional_value_at_risk_percent=_conditional_value_at_risk(
            returns, confidence_level_percent
        ),
    )


def _percentile(sorted_values: list[float], percentile: float) -> float:
    if len(sorted_values) == 1:
        return sorted_values[0]

    rank = (percentile / 100) * (len(sorted_values) - 1)
    lower_index = int(rank)
    upper_index = min(lower_index + 1, len(sorted_values) - 1)
    fraction = rank - lower_index
    lower_value = sorted_values[lower_index]
    upper_value = sorted_values[upper_index]
    return lower_value + (upper_value - lower_value) * fraction


def _confidence_interval(
    sorted_returns: list[float], confidence_level_percent: float
) -> ConfidenceInterval:
    tail = (100 - confidence_level_percent) / 2
    return ConfidenceInterval(
        confidence_level_percent=confidence_level_percent,
        lower_bound=_percentile(sorted_returns, tail),
        upper_bound=_percentile(sorted_returns, 100 - tail),
    )


def _value_at_risk(sorted_returns: list[float], confidence_level_percent: float) -> float:
    tail_percentile = 100 - confidence_level_percent
    threshold = _percentile(sorted_returns, tail_percentile)
    return -threshold if threshold < 0 else 0.0


def _conditional_value_at_risk(
    sorted_returns: list[float], confidence_level_percent: float
) -> float:
    tail_percentile = 100 - confidence_level_percent
    threshold = _percentile(sorted_returns, tail_percentile)
    tail_losses = [value for value in sorted_returns if value <= threshold]
    if not tail_losses:
        return 0.0
    tail_mean = stats.fmean(tail_losses)
    return -tail_mean if tail_mean < 0 else 0.0
