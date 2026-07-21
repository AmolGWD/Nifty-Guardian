from datetime import datetime

from app.trading.analytics.periodic_analysis import (
    analyze_monthly_performance,
    analyze_yearly_performance,
)
from tests.trading.analytics.helpers import make_equity_point, make_trade


def test_yearly_performance_matches_hand_calculated_values() -> None:
    trades = [
        make_trade(exit_time=datetime(2025, 3, 1, 10, 0), pnl=1_000.0),
        make_trade(exit_time=datetime(2025, 6, 1, 10, 0), pnl=-500.0),
        make_trade(exit_time=datetime(2026, 3, 1, 10, 0), pnl=2_000.0),
    ]
    equity_curve = [
        make_equity_point(timestamp=datetime(2025, 1, 1, 9, 0), equity=100_000.0),
        make_equity_point(timestamp=datetime(2025, 12, 31, 15, 0), equity=100_500.0),
        make_equity_point(timestamp=datetime(2026, 1, 1, 9, 0), equity=100_500.0),
        make_equity_point(timestamp=datetime(2026, 12, 31, 15, 0), equity=102_500.0),
    ]

    yearly = analyze_yearly_performance(trades, equity_curve)

    assert [period.year for period in yearly] == [2025, 2026]
    assert yearly[0].trades == 2
    assert yearly[0].net_profit == 500.0
    assert yearly[0].win_rate == 50.0
    assert yearly[1].trades == 1
    assert yearly[1].net_profit == 2_000.0


def test_monthly_performance_matches_hand_calculated_values() -> None:
    trades = [
        make_trade(exit_time=datetime(2026, 7, 5, 10, 0), pnl=300.0),
        make_trade(exit_time=datetime(2026, 7, 20, 10, 0), pnl=-100.0),
        make_trade(exit_time=datetime(2026, 8, 3, 10, 0), pnl=400.0),
    ]
    equity_curve = [
        make_equity_point(timestamp=datetime(2026, 7, 1, 9, 0), equity=100_000.0),
        make_equity_point(timestamp=datetime(2026, 7, 31, 15, 0), equity=100_200.0),
        make_equity_point(timestamp=datetime(2026, 8, 1, 9, 0), equity=100_200.0),
        make_equity_point(timestamp=datetime(2026, 8, 31, 15, 0), equity=100_600.0),
    ]

    monthly = analyze_monthly_performance(trades, equity_curve)

    assert [(period.year, period.month) for period in monthly] == [(2026, 7), (2026, 8)]
    assert monthly[0].trade_count == 2
    assert monthly[0].net_pnl == 200.0
    assert monthly[1].trade_count == 1
    assert monthly[1].net_pnl == 400.0


def test_yearly_and_monthly_performance_are_empty_without_equity_data() -> None:
    assert analyze_yearly_performance([], []) == []
    assert analyze_monthly_performance([], []) == []
