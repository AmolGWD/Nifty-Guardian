from datetime import datetime

from app.trading.analytics.risk_analysis import analyze_risk
from tests.trading.analytics.helpers import make_equity_point, make_trade


def test_analyze_risk_matches_hand_calculated_streaks() -> None:
    trades = [
        make_trade(pnl=100.0),
        make_trade(pnl=100.0),
        make_trade(pnl=100.0),
        make_trade(pnl=-50.0),
        make_trade(pnl=-50.0),
        make_trade(pnl=100.0),
    ]
    equity_curve = [
        make_equity_point(timestamp=datetime(2026, 7, 21, 9, 0), equity=100_000.0),
        make_equity_point(timestamp=datetime(2026, 7, 21, 10, 0), equity=95_000.0),
        make_equity_point(timestamp=datetime(2026, 7, 21, 11, 0), equity=100_000.0),
    ]

    result = analyze_risk(trades, equity_curve)

    assert result.longest_winning_streak == 3
    assert result.longest_losing_streak == 2
    assert result.average_winning_streak == (3 + 1) / 2
    assert result.average_losing_streak == 2.0
    assert result.largest_equity_peak == 100_000.0
    assert result.largest_equity_valley == 95_000.0
    assert len(result.drawdown_episodes) == 1


def test_analyze_risk_handles_no_trades() -> None:
    result = analyze_risk([], [])

    assert result.longest_winning_streak == 0
    assert result.longest_losing_streak == 0
    assert result.average_winning_streak == 0.0
    assert result.average_losing_streak == 0.0
    assert result.drawdown_episodes == []
