"""
Trade distribution: holding time, Long/Short split, and exit-reason
breakdown (Stop Loss %, Target %, End Of Day %) - all read directly
from `BacktestTrade` fields, no recomputation of any indicator,
strategy, or risk figure.
"""

import statistics

from app.trading.analytics.models import DirectionBucket, ExitReasonBucket, TradeDistribution
from app.trading.backtest.models import BacktestTrade, ExitReason


def analyze_trade_distribution(trades: list[BacktestTrade]) -> TradeDistribution:
    if not trades:
        return TradeDistribution(
            average_holding_minutes=0.0,
            median_holding_minutes=0.0,
            longest_holding_minutes=0.0,
            shortest_holding_minutes=0.0,
            by_direction=[],
            by_exit_reason=[],
            stop_loss_percent=0.0,
            target_percent=0.0,
            end_of_day_percent=0.0,
        )

    holding_minutes = [
        (trade.exit_time - trade.entry_time).total_seconds() / 60 for trade in trades
    ]

    total = len(trades)
    stop_loss_count = sum(1 for trade in trades if trade.exit_reason == ExitReason.STOP_LOSS)
    target_count = sum(1 for trade in trades if trade.exit_reason == ExitReason.TARGET)
    end_of_day_count = sum(1 for trade in trades if trade.exit_reason == ExitReason.END_OF_DAY)

    return TradeDistribution(
        average_holding_minutes=round(sum(holding_minutes) / total, 4),
        median_holding_minutes=round(statistics.median(holding_minutes), 4),
        longest_holding_minutes=round(max(holding_minutes), 4),
        shortest_holding_minutes=round(min(holding_minutes), 4),
        by_direction=_direction_buckets(trades),
        by_exit_reason=_exit_reason_buckets(trades),
        stop_loss_percent=round(stop_loss_count / total * 100, 4),
        target_percent=round(target_count / total * 100, 4),
        end_of_day_percent=round(end_of_day_count / total * 100, 4),
    )


def _direction_buckets(trades: list[BacktestTrade]) -> list[DirectionBucket]:
    groups: dict[str, list[BacktestTrade]] = {}
    for trade in trades:
        groups.setdefault(trade.direction.value, []).append(trade)

    buckets = []
    for group_trades in groups.values():
        wins = [trade for trade in group_trades if trade.pnl > 0]
        buckets.append(
            DirectionBucket(
                direction=group_trades[0].direction,
                trade_count=len(group_trades),
                win_rate=round(len(wins) / len(group_trades) * 100, 4),
                net_pnl=round(sum(trade.pnl for trade in group_trades), 4),
            )
        )
    return buckets


def _exit_reason_buckets(trades: list[BacktestTrade]) -> list[ExitReasonBucket]:
    total = len(trades)
    groups: dict[str, int] = {}
    for trade in trades:
        groups[trade.exit_reason.value] = groups.get(trade.exit_reason.value, 0) + 1

    return [
        ExitReasonBucket(
            exit_reason=reason,
            trade_count=count,
            percentage=round(count / total * 100, 4),
        )
        for reason, count in groups.items()
    ]
