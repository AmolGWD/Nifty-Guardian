"""
Per-strategy breakdown - trade count, win rate, net P&L, and profit
factor grouped by `BacktestTrade.strategy_name`. Only one strategy
(EMABreakout) is registered today, but the Strategy Engine is a plugin
architecture (Phase 8) that expects more - this groups generically so
a second registered strategy needs no change here.
"""

from app.trading.analytics.models import StrategyPerformance
from app.trading.backtest.models import BacktestTrade


def analyze_strategies(trades: list[BacktestTrade]) -> list[StrategyPerformance]:
    groups: dict[str, list[BacktestTrade]] = {}
    for trade in trades:
        groups.setdefault(trade.strategy_name, []).append(trade)

    performances = []
    for strategy_name, group_trades in groups.items():
        wins = [trade for trade in group_trades if trade.pnl > 0]
        losses = [trade for trade in group_trades if trade.pnl < 0]

        gross_profit = sum(trade.pnl for trade in wins)
        gross_loss = abs(sum(trade.pnl for trade in losses))
        profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else None

        performances.append(
            StrategyPerformance(
                strategy_name=strategy_name,
                trade_count=len(group_trades),
                win_rate=round(len(wins) / len(group_trades) * 100, 4),
                net_pnl=round(sum(trade.pnl for trade in group_trades), 4),
                profit_factor=round(profit_factor, 4) if profit_factor is not None else None,
            )
        )

    return performances
