"""
Computes performance statistics from a completed backtest's trade
history and equity curve. Pure arithmetic over already-simulated
results - no indicator, strategy, or risk calculation happens here.
"""

from datetime import date

from app.trading.backtest.models import BacktestTrade, DailyPnL, EquityPoint, PerformanceReport

_TRADING_DAYS_PER_YEAR = 252


def build_performance_report(
    initial_capital: float,
    final_capital: float,
    trades: list[BacktestTrade],
    equity_curve: list[EquityPoint],
) -> PerformanceReport:
    total_trades = len(trades)
    wins = [trade for trade in trades if trade.pnl > 0]
    losses = [trade for trade in trades if trade.pnl < 0]

    winning_trades = len(wins)
    losing_trades = len(losses)
    win_rate = (winning_trades / total_trades * 100) if total_trades else 0.0

    average_win = (sum(trade.pnl for trade in wins) / winning_trades) if winning_trades else 0.0
    average_loss = (sum(trade.pnl for trade in losses) / losing_trades) if losing_trades else 0.0
    largest_win = max((trade.pnl for trade in wins), default=0.0)
    largest_loss = min((trade.pnl for trade in losses), default=0.0)

    gross_profit = sum(trade.pnl for trade in wins)
    gross_loss = abs(sum(trade.pnl for trade in losses))
    profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else None

    net_profit = final_capital - initial_capital
    expectancy = (net_profit / total_trades) if total_trades else 0.0

    average_reward_risk_ratio = (
        sum(trade.planned_reward_risk_ratio for trade in trades) / total_trades
        if total_trades
        else 0.0
    )

    max_drawdown = calculate_max_drawdown(equity_curve)
    max_consecutive_wins, max_consecutive_losses = calculate_streaks(trades)
    sharpe_ratio = calculate_sharpe_ratio(equity_curve)

    return PerformanceReport(
        initial_capital=initial_capital,
        final_capital=final_capital,
        net_profit=round(net_profit, 4),
        total_trades=total_trades,
        winning_trades=winning_trades,
        losing_trades=losing_trades,
        win_rate=round(win_rate, 4),
        average_win=round(average_win, 4),
        average_loss=round(average_loss, 4),
        largest_win=round(largest_win, 4),
        largest_loss=round(largest_loss, 4),
        profit_factor=round(profit_factor, 4) if profit_factor is not None else None,
        expectancy=round(expectancy, 4),
        average_reward_risk_ratio=round(average_reward_risk_ratio, 4),
        max_drawdown=round(max_drawdown, 4),
        max_consecutive_wins=max_consecutive_wins,
        max_consecutive_losses=max_consecutive_losses,
        sharpe_ratio=round(sharpe_ratio, 4) if sharpe_ratio is not None else None,
    )


def calculate_max_drawdown(equity_curve: list[EquityPoint]) -> float:
    if not equity_curve:
        return 0.0

    peak = equity_curve[0].equity
    max_drawdown = 0.0

    for point in equity_curve:
        peak = max(peak, point.equity)
        max_drawdown = max(max_drawdown, peak - point.equity)

    return max_drawdown


def calculate_streaks(trades: list[BacktestTrade]) -> tuple[int, int]:
    max_win_streak = 0
    max_loss_streak = 0
    current_win_streak = 0
    current_loss_streak = 0

    for trade in trades:
        if trade.pnl > 0:
            current_win_streak += 1
            current_loss_streak = 0
        elif trade.pnl < 0:
            current_loss_streak += 1
            current_win_streak = 0
        else:
            current_win_streak = 0
            current_loss_streak = 0

        max_win_streak = max(max_win_streak, current_win_streak)
        max_loss_streak = max(max_loss_streak, current_loss_streak)

    return max_win_streak, max_loss_streak


def calculate_sharpe_ratio(equity_curve: list[EquityPoint]) -> float | None:
    """
    Annualized Sharpe ratio from daily simple returns (last equity
    value seen each calendar day). Returns None when there isn't
    enough data to make the number meaningful (fewer than 3 daily
    equity points, fewer than 2 resulting returns, or zero variance) -
    a missing Sharpe ratio is more honest than a misleading one.
    """
    daily_equities = _last_equity_per_day(equity_curve)
    if len(daily_equities) < 3:
        return None

    returns = [
        (daily_equities[i] - daily_equities[i - 1]) / daily_equities[i - 1]
        for i in range(1, len(daily_equities))
        if daily_equities[i - 1] != 0
    ]
    if len(returns) < 2:
        return None

    mean_return = sum(returns) / len(returns)
    variance = sum((r - mean_return) ** 2 for r in returns) / (len(returns) - 1)
    std_dev = variance**0.5
    if std_dev == 0:
        return None

    sharpe: float = (mean_return / std_dev) * (_TRADING_DAYS_PER_YEAR**0.5)
    return sharpe


def _last_equity_per_day(equity_curve: list[EquityPoint]) -> list[float]:
    per_day: dict[date, float] = {}
    order: list[date] = []

    for point in equity_curve:
        day = point.timestamp.date()
        if day not in per_day:
            order.append(day)
        per_day[day] = point.equity

    return [per_day[day] for day in order]


def compute_daily_pnl(trades: list[BacktestTrade]) -> list[DailyPnL]:
    totals: dict[date, float] = {}
    order: list[date] = []

    for trade in trades:
        day = trade.exit_time.date()
        if day not in totals:
            order.append(day)
            totals[day] = 0.0
        totals[day] += trade.pnl

    return [DailyPnL(date=day, pnl=round(totals[day], 4)) for day in order]
