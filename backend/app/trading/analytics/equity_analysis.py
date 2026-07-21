"""
Statistics derived purely from the equity curve: total return, elapsed
time span, daily returns (shared by Sharpe/Sortino-style ratios), and
the largest peak/valley the equity curve ever reached.

A single pass over the equity curve throughout - O(n) in the number of
candles evaluated, never O(n^2) - so this stays practical across
several years of history.
"""

from datetime import date

from app.trading.backtest.models import EquityPoint

_DAYS_PER_YEAR = 365.25


def calculate_total_return_percent(initial_capital: float, final_capital: float) -> float:
    if initial_capital == 0:
        return 0.0
    return (final_capital - initial_capital) / initial_capital * 100


def calculate_years_elapsed(equity_curve: list[EquityPoint]) -> float | None:
    if len(equity_curve) < 2:
        return None

    span_days = (equity_curve[-1].timestamp - equity_curve[0].timestamp).days
    if span_days <= 0:
        return None

    return span_days / _DAYS_PER_YEAR


def last_equity_per_day(equity_curve: list[EquityPoint]) -> list[float]:
    per_day: dict[date, float] = {}
    order: list[date] = []

    for point in equity_curve:
        day = point.timestamp.date()
        if day not in per_day:
            order.append(day)
        per_day[day] = point.equity

    return [per_day[day] for day in order]


def daily_returns(equity_curve: list[EquityPoint]) -> list[float]:
    daily_equities = last_equity_per_day(equity_curve)
    return [
        (daily_equities[i] - daily_equities[i - 1]) / daily_equities[i - 1]
        for i in range(1, len(daily_equities))
        if daily_equities[i - 1] != 0
    ]


def largest_equity_peak(equity_curve: list[EquityPoint]) -> float:
    if not equity_curve:
        return 0.0
    return max(point.equity for point in equity_curve)


def largest_equity_valley(equity_curve: list[EquityPoint]) -> float:
    if not equity_curve:
        return 0.0
    return min(point.equity for point in equity_curve)
