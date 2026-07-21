from datetime import datetime

from app.trading.analytics.models import (
    AnalyticsReport,
    MarketRegimeAnalysis,
    MonthlyPerformance,
    OverallPerformance,
    RiskAnalysis,
    TimeAnalysis,
    YearlyPerformance,
)
from app.trading.analytics.report_builder import format_analytics_report
from app.trading.analytics.strategy_analysis import analyze_strategies
from app.trading.analytics.trade_distribution import analyze_trade_distribution
from app.trading.backtest.models import BacktestResult, DailyPnL, PerformanceReport
from tests.trading.analytics.helpers import make_backtest_config, make_equity_point, make_trade


def _make_minimal_report() -> AnalyticsReport:
    trades = [make_trade(pnl=500.0), make_trade(pnl=-200.0)]

    overall = OverallPerformance(
        initial_capital=100_000.0,
        final_capital=100_300.0,
        cagr=None,
        annual_return=None,
        net_profit=300.0,
        total_return_percent=0.3,
        total_trades=2,
        winning_trades=1,
        losing_trades=1,
        win_rate=50.0,
        profit_factor=2.5,
        expectancy=150.0,
        average_win=500.0,
        average_loss=-200.0,
        largest_win=500.0,
        largest_loss=-200.0,
        reward_risk=2.0,
        sharpe_ratio=None,
        sortino_ratio=None,
        calmar_ratio=None,
        recovery_factor=None,
        max_drawdown=200.0,
    )

    return AnalyticsReport(
        overall=overall,
        yearly=[
            YearlyPerformance(
                year=2026, trades=2, win_rate=50.0, net_profit=300.0,
                return_percent=0.3, max_drawdown=200.0,
            )
        ],
        monthly=[
            MonthlyPerformance(
                year=2026, month=7, trade_count=2, win_rate=50.0,
                net_pnl=300.0, return_percent=0.3,
            )
        ],
        market_regimes=MarketRegimeAnalysis(by_trend=[], by_volatility=[], by_momentum=[]),
        time_analysis=TimeAnalysis(
            by_hour=[], by_weekday=[], by_session=[], by_expiry=[],
            best_hour=None, worst_hour=None, best_weekday=None, worst_weekday=None,
        ),
        trade_distribution=analyze_trade_distribution(trades),
        risk_analysis=RiskAnalysis(
            longest_winning_streak=1,
            longest_losing_streak=1,
            average_winning_streak=1.0,
            average_losing_streak=1.0,
            drawdown_episodes=[],
            largest_equity_peak=100_500.0,
            largest_equity_valley=99_800.0,
        ),
        strategies=analyze_strategies(trades),
    )


def _make_minimal_result() -> BacktestResult:
    config = make_backtest_config()
    equity_curve = [
        make_equity_point(timestamp=datetime(2026, 7, 21, 9, 0), equity=100_000.0),
        make_equity_point(timestamp=datetime(2026, 7, 21, 15, 0), equity=100_300.0),
    ]
    return BacktestResult(
        config=config,
        trades=[make_trade(pnl=500.0), make_trade(pnl=-200.0)],
        equity_curve=equity_curve,
        daily_pnl=[DailyPnL(date=datetime(2026, 7, 21).date(), pnl=300.0)],
        report=PerformanceReport(
            initial_capital=100_000.0,
            final_capital=100_300.0,
            net_profit=300.0,
            total_trades=2,
            winning_trades=1,
            losing_trades=1,
            win_rate=50.0,
            average_win=500.0,
            average_loss=-200.0,
            largest_win=500.0,
            largest_loss=-200.0,
            profit_factor=2.5,
            expectancy=150.0,
            average_reward_risk_ratio=2.0,
            max_drawdown=200.0,
            max_consecutive_wins=1,
            max_consecutive_losses=1,
            sharpe_ratio=None,
        ),
    )


def test_format_analytics_report_includes_every_section() -> None:
    analytics = _make_minimal_report()
    result = _make_minimal_result()

    output = format_analytics_report(analytics, result)

    for heading in (
        "OVERALL PERFORMANCE",
        "YEARLY PERFORMANCE",
        "MONTHLY PERFORMANCE",
        "MARKET REGIME ANALYSIS",
        "TIME ANALYSIS",
        "TRADE DISTRIBUTION",
        "RISK ANALYSIS",
        "STRATEGY BREAKDOWN",
        "EQUITY CURVE",
        "DRAWDOWN CURVE",
        "MONTHLY RETURNS",
        "TRADE DISTRIBUTION CHART",
    ):
        assert heading in output


def test_format_analytics_report_handles_missing_optional_metrics() -> None:
    analytics = _make_minimal_report()
    result = _make_minimal_result()

    output = format_analytics_report(analytics, result)

    assert "N/A" in output
