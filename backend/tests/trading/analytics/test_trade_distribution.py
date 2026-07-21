from datetime import datetime

from app.trading.analytics.trade_distribution import analyze_trade_distribution
from app.trading.backtest.models import ExitReason
from app.trading.strategy.models import StrategyDirection
from tests.trading.analytics.helpers import make_trade


def test_analyze_trade_distribution_matches_hand_calculated_values() -> None:
    trades = [
        make_trade(
            entry_time=datetime(2026, 7, 21, 9, 30),
            exit_time=datetime(2026, 7, 21, 10, 0),
            exit_reason=ExitReason.TARGET,
            pnl=500.0,
        ),
        make_trade(
            entry_time=datetime(2026, 7, 21, 10, 0),
            exit_time=datetime(2026, 7, 21, 10, 30),
            exit_reason=ExitReason.STOP_LOSS,
            pnl=-200.0,
        ),
        make_trade(
            entry_time=datetime(2026, 7, 21, 11, 0),
            exit_time=datetime(2026, 7, 21, 12, 0),
            exit_reason=ExitReason.END_OF_DAY,
            pnl=100.0,
        ),
    ]

    distribution = analyze_trade_distribution(trades)

    assert distribution.average_holding_minutes == 40.0
    assert distribution.longest_holding_minutes == 60.0
    assert distribution.shortest_holding_minutes == 30.0
    assert distribution.stop_loss_percent == round(1 / 3 * 100, 4)
    assert distribution.target_percent == round(1 / 3 * 100, 4)
    assert distribution.end_of_day_percent == round(1 / 3 * 100, 4)
    assert len(distribution.by_exit_reason) == 3
    assert len(distribution.by_direction) == 1
    assert distribution.by_direction[0].direction == StrategyDirection.LONG
    assert distribution.by_direction[0].trade_count == 3


def test_analyze_trade_distribution_handles_empty_trades() -> None:
    distribution = analyze_trade_distribution([])

    assert distribution.average_holding_minutes == 0.0
    assert distribution.by_direction == []
    assert distribution.by_exit_reason == []
