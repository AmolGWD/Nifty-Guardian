from app.trading.analytics.strategy_analysis import analyze_strategies
from tests.trading.analytics.helpers import make_trade


def test_analyze_strategies_groups_by_strategy_name() -> None:
    trades = [
        make_trade(strategy_name="EMABreakout", pnl=500.0),
        make_trade(strategy_name="EMABreakout", pnl=-200.0),
        make_trade(strategy_name="OtherStrategy", pnl=300.0),
    ]

    strategies = {s.strategy_name: s for s in analyze_strategies(trades)}

    assert strategies["EMABreakout"].trade_count == 2
    assert strategies["EMABreakout"].net_pnl == 300.0
    assert strategies["EMABreakout"].win_rate == 50.0
    assert strategies["EMABreakout"].profit_factor == 2.5
    assert strategies["OtherStrategy"].trade_count == 1
    assert strategies["OtherStrategy"].profit_factor is None


def test_analyze_strategies_handles_no_trades() -> None:
    assert analyze_strategies([]) == []
