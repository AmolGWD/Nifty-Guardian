"""
Year-by-year and month-by-month performance, grouping trades and the
equity curve by calendar period. Reuses Phase 11's own
`calculate_max_drawdown()` on each period's equity-curve slice rather
than reimplementing drawdown detection a second time.
"""

from app.trading.analytics.models import MonthlyPerformance, YearlyPerformance
from app.trading.backtest.models import BacktestTrade, EquityPoint
from app.trading.backtest.performance import calculate_max_drawdown


def analyze_yearly_performance(
    trades: list[BacktestTrade], equity_curve: list[EquityPoint]
) -> list[YearlyPerformance]:
    years = sorted({point.timestamp.year for point in equity_curve})

    results = []
    for year in years:
        year_trades = [trade for trade in trades if trade.exit_time.year == year]
        year_equity = [point for point in equity_curve if point.timestamp.year == year]
        if not year_equity:
            continue

        wins = [trade for trade in year_trades if trade.pnl > 0]
        win_rate = (len(wins) / len(year_trades) * 100) if year_trades else 0.0
        net_profit = sum(trade.pnl for trade in year_trades)

        start_equity = year_equity[0].equity
        end_equity = year_equity[-1].equity
        return_percent = (
            ((end_equity - start_equity) / start_equity * 100) if start_equity else 0.0
        )

        results.append(
            YearlyPerformance(
                year=year,
                trades=len(year_trades),
                win_rate=round(win_rate, 4),
                net_profit=round(net_profit, 4),
                return_percent=round(return_percent, 4),
                max_drawdown=round(calculate_max_drawdown(year_equity), 4),
            )
        )

    return results


def analyze_monthly_performance(
    trades: list[BacktestTrade], equity_curve: list[EquityPoint]
) -> list[MonthlyPerformance]:
    periods = sorted({(point.timestamp.year, point.timestamp.month) for point in equity_curve})

    results = []
    for year, month in periods:
        period_trades = [
            trade
            for trade in trades
            if (trade.exit_time.year, trade.exit_time.month) == (year, month)
        ]
        period_equity = [
            point
            for point in equity_curve
            if (point.timestamp.year, point.timestamp.month) == (year, month)
        ]
        if not period_equity:
            continue

        wins = [trade for trade in period_trades if trade.pnl > 0]
        win_rate = (len(wins) / len(period_trades) * 100) if period_trades else 0.0
        net_pnl = sum(trade.pnl for trade in period_trades)

        start_equity = period_equity[0].equity
        end_equity = period_equity[-1].equity
        return_percent = (
            ((end_equity - start_equity) / start_equity * 100) if start_equity else 0.0
        )

        results.append(
            MonthlyPerformance(
                year=year,
                month=month,
                trade_count=len(period_trades),
                win_rate=round(win_rate, 4),
                net_pnl=round(net_pnl, 4),
                return_percent=round(return_percent, 4),
            )
        )

    return results
