from datetime import datetime

from app.trading.backtest.models import BacktestTrade, EquityPoint, ExitReason
from app.trading.backtest.performance import (
    build_performance_report,
    calculate_max_drawdown,
    calculate_sharpe_ratio,
    calculate_streaks,
    compute_daily_pnl,
)
from app.trading.strategy.models import StrategyDirection

_BASE_TIME = datetime(2026, 7, 21, 10, 0)


def make_trade(
    *, pnl: float, exit_time: datetime = _BASE_TIME, reward_risk_ratio: float = 2.0
) -> BacktestTrade:
    return BacktestTrade(
        strategy_name="EMABreakout",
        direction=StrategyDirection.LONG,
        entry_time=_BASE_TIME,
        entry_price=100.0,
        exit_time=exit_time,
        exit_price=100.0 + pnl,
        exit_reason=ExitReason.TARGET,
        quantity=1,
        stop_loss=95.0,
        target=110.0,
        planned_reward_risk_ratio=reward_risk_ratio,
        pnl=pnl,
    )


def test_build_performance_report_matches_hand_calculated_values() -> None:
    trades = [
        make_trade(pnl=500.0),
        make_trade(pnl=-200.0),
        make_trade(pnl=300.0),
        make_trade(pnl=-100.0),
        make_trade(pnl=400.0),
    ]
    equity_curve = [EquityPoint(timestamp=_BASE_TIME, equity=100_900.0)]

    report = build_performance_report(100_000.0, 100_900.0, trades, equity_curve)

    assert report.total_trades == 5
    assert report.winning_trades == 3
    assert report.losing_trades == 2
    assert report.win_rate == 60.0
    assert report.average_win == 400.0
    assert report.average_loss == -150.0
    assert report.largest_win == 500.0
    assert report.largest_loss == -200.0
    assert report.profit_factor == 4.0
    assert report.net_profit == 900.0
    assert report.expectancy == 180.0
    assert report.average_reward_risk_ratio == 2.0


def test_build_performance_report_with_no_trades() -> None:
    report = build_performance_report(100_000.0, 100_000.0, [], [])

    assert report.total_trades == 0
    assert report.win_rate == 0.0
    assert report.profit_factor is None
    assert report.expectancy == 0.0
    assert report.max_drawdown == 0.0


def test_calculate_max_drawdown_matches_hand_calculated_value() -> None:
    equity_curve = [
        EquityPoint(timestamp=_BASE_TIME, equity=100_000.0),
        EquityPoint(timestamp=_BASE_TIME, equity=105_000.0),
        EquityPoint(timestamp=_BASE_TIME, equity=98_000.0),
        EquityPoint(timestamp=_BASE_TIME, equity=101_000.0),
    ]

    assert calculate_max_drawdown(equity_curve) == 7_000.0


def test_calculate_max_drawdown_is_zero_for_empty_curve() -> None:
    assert calculate_max_drawdown([]) == 0.0


def test_calculate_streaks_matches_hand_calculated_value() -> None:
    trades = [
        make_trade(pnl=100.0),
        make_trade(pnl=100.0),
        make_trade(pnl=100.0),
        make_trade(pnl=-50.0),
        make_trade(pnl=-50.0),
        make_trade(pnl=100.0),
    ]

    max_win_streak, max_loss_streak = calculate_streaks(trades)

    assert max_win_streak == 3
    assert max_loss_streak == 2


def test_calculate_sharpe_ratio_is_none_with_insufficient_data() -> None:
    equity_curve = [
        EquityPoint(timestamp=datetime(2026, 7, 21, 10, 0), equity=100_000.0),
        EquityPoint(timestamp=datetime(2026, 7, 22, 10, 0), equity=101_000.0),
    ]

    assert calculate_sharpe_ratio(equity_curve) is None


def test_calculate_sharpe_ratio_is_none_when_variance_is_zero() -> None:
    equity_curve = [
        EquityPoint(timestamp=datetime(2026, 7, 21, 10, 0), equity=100_000.0),
        EquityPoint(timestamp=datetime(2026, 7, 22, 10, 0), equity=100_000.0),
        EquityPoint(timestamp=datetime(2026, 7, 23, 10, 0), equity=100_000.0),
    ]

    assert calculate_sharpe_ratio(equity_curve) is None


def test_calculate_sharpe_ratio_is_a_float_with_varying_returns() -> None:
    equity_curve = [
        EquityPoint(timestamp=datetime(2026, 7, 21, 10, 0), equity=100_000.0),
        EquityPoint(timestamp=datetime(2026, 7, 22, 10, 0), equity=101_000.0),
        EquityPoint(timestamp=datetime(2026, 7, 23, 10, 0), equity=99_500.0),
        EquityPoint(timestamp=datetime(2026, 7, 24, 10, 0), equity=102_000.0),
    ]

    sharpe = calculate_sharpe_ratio(equity_curve)

    assert sharpe is not None
    assert isinstance(sharpe, float)


def test_compute_daily_pnl_groups_by_exit_date() -> None:
    trades = [
        make_trade(pnl=100.0, exit_time=datetime(2026, 7, 21, 11, 0)),
        make_trade(pnl=-40.0, exit_time=datetime(2026, 7, 21, 14, 0)),
        make_trade(pnl=200.0, exit_time=datetime(2026, 7, 22, 10, 0)),
    ]

    daily_pnl = compute_daily_pnl(trades)

    assert len(daily_pnl) == 2
    assert daily_pnl[0].date == datetime(2026, 7, 21).date()
    assert daily_pnl[0].pnl == 60.0
    assert daily_pnl[1].date == datetime(2026, 7, 22).date()
    assert daily_pnl[1].pnl == 200.0
