"""
Streak statistics, drawdown episodes, and equity extremes. Longest
win/loss streaks reuse Phase 11's own `calculate_streaks()` directly
rather than recomputing the running-max logic a second time; average
streak length is new (Phase 11 only ever kept the running maximum, not
every individual streak's length).
"""

from app.trading.analytics.drawdown import identify_drawdown_episodes
from app.trading.analytics.equity_analysis import largest_equity_peak, largest_equity_valley
from app.trading.analytics.models import RiskAnalysis
from app.trading.backtest.models import BacktestTrade, EquityPoint
from app.trading.backtest.performance import calculate_streaks


def analyze_risk(trades: list[BacktestTrade], equity_curve: list[EquityPoint]) -> RiskAnalysis:
    longest_winning_streak, longest_losing_streak = calculate_streaks(trades)
    winning_streaks, losing_streaks = _all_streak_lengths(trades)

    return RiskAnalysis(
        longest_winning_streak=longest_winning_streak,
        longest_losing_streak=longest_losing_streak,
        average_winning_streak=round(_average(winning_streaks), 4),
        average_losing_streak=round(_average(losing_streaks), 4),
        drawdown_episodes=identify_drawdown_episodes(equity_curve),
        largest_equity_peak=round(largest_equity_peak(equity_curve), 4),
        largest_equity_valley=round(largest_equity_valley(equity_curve), 4),
    )


def _all_streak_lengths(trades: list[BacktestTrade]) -> tuple[list[int], list[int]]:
    winning_streaks: list[int] = []
    losing_streaks: list[int] = []
    current_streak = 0
    current_is_win: bool | None = None

    for trade in trades:
        is_win = trade.pnl > 0
        is_loss = trade.pnl < 0

        if not is_win and not is_loss:
            if current_is_win is True:
                winning_streaks.append(current_streak)
            elif current_is_win is False:
                losing_streaks.append(current_streak)
            current_streak = 0
            current_is_win = None
            continue

        if current_is_win == is_win:
            current_streak += 1
        else:
            if current_is_win is True:
                winning_streaks.append(current_streak)
            elif current_is_win is False:
                losing_streaks.append(current_streak)
            current_streak = 1
            current_is_win = is_win

    if current_is_win is True:
        winning_streaks.append(current_streak)
    elif current_is_win is False:
        losing_streaks.append(current_streak)

    return winning_streaks, losing_streaks


def _average(values: list[int]) -> float:
    if not values:
        return 0.0
    return sum(values) / len(values)
