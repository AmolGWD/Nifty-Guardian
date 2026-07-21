"""
Overall-performance metrics that Phase 11's PerformanceReport doesn't
already compute: CAGR, (linear) Annual Return, Sortino Ratio, Calmar
Ratio, Recovery Factor. Metrics Phase 11 already computes (Sharpe
Ratio, Max Drawdown, win/loss counts, profit factor, expectancy, ...)
are read directly from `BacktestResult.report` by `analytics_engine.py`
rather than recalculated here - reusing an existing result, not
duplicating the logic that produced it.
"""

from app.trading.analytics.equity_analysis import daily_returns
from app.trading.backtest.models import EquityPoint

_TRADING_DAYS_PER_YEAR = 252


def calculate_cagr(
    initial_capital: float, final_capital: float, years: float | None
) -> float | None:
    if years is None or years <= 0 or initial_capital <= 0 or final_capital <= 0:
        return None

    growth = final_capital / initial_capital
    cagr: float = growth ** (1 / years) - 1
    return cagr * 100


def calculate_annual_return(
    net_profit: float, initial_capital: float, years: float | None
) -> float | None:
    if years is None or years <= 0 or initial_capital <= 0:
        return None

    annual_return: float = (net_profit / initial_capital) / years
    return annual_return * 100


def calculate_sortino_ratio(equity_curve: list[EquityPoint]) -> float | None:
    """
    Same annualization convention as Phase 11's Sharpe Ratio (daily
    simple returns from the equity curve, scaled by sqrt(252)), but the
    denominator is downside deviation - the standard deviation of only
    the negative returns - so upside volatility never penalizes the
    ratio. Returns None under the same "not enough data to be
    meaningful" conditions Phase 11 uses for Sharpe.
    """
    returns = daily_returns(equity_curve)
    if len(returns) < 2:
        return None

    downside_returns = [r for r in returns if r < 0]
    if len(downside_returns) < 2:
        return None

    mean_return = sum(returns) / len(returns)
    downside_variance = sum(r**2 for r in downside_returns) / len(downside_returns)
    downside_deviation = downside_variance**0.5
    if downside_deviation == 0:
        return None

    sortino: float = (mean_return / downside_deviation) * (_TRADING_DAYS_PER_YEAR**0.5)
    return sortino


def calculate_calmar_ratio(cagr_percent: float | None, max_drawdown_percent: float) -> float | None:
    if cagr_percent is None or max_drawdown_percent <= 0:
        return None
    return cagr_percent / max_drawdown_percent


def calculate_recovery_factor(net_profit: float, max_drawdown: float) -> float | None:
    if max_drawdown <= 0:
        return None
    return net_profit / max_drawdown
