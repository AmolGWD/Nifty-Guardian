from datetime import datetime

from app.trading.backtest.models import (
    BacktestConfig,
    BacktestResult,
    BacktestTrade,
    ExitReason,
    PerformanceReport,
)
from app.trading.backtest.report import format_report, format_trade
from app.trading.strategy.models import StrategyDirection
from tests.trading.backtest.helpers import make_risk_config


def make_report(
    *, profit_factor: float | None = 2.0, sharpe_ratio: float | None = 1.2
) -> PerformanceReport:
    return PerformanceReport(
        initial_capital=100_000.0,
        final_capital=105_000.0,
        net_profit=5_000.0,
        total_trades=10,
        winning_trades=6,
        losing_trades=4,
        win_rate=60.0,
        average_win=1_500.0,
        average_loss=-750.0,
        largest_win=3_000.0,
        largest_loss=-1_200.0,
        profit_factor=profit_factor,
        expectancy=500.0,
        average_reward_risk_ratio=2.0,
        max_drawdown=2_500.0,
        max_consecutive_wins=3,
        max_consecutive_losses=2,
        sharpe_ratio=sharpe_ratio,
    )


def make_trade() -> BacktestTrade:
    return BacktestTrade(
        strategy_name="EMABreakout",
        direction=StrategyDirection.LONG,
        entry_time=datetime(2026, 7, 21, 10, 0),
        entry_price=100.0,
        exit_time=datetime(2026, 7, 21, 11, 0),
        exit_price=106.0,
        exit_reason=ExitReason.TARGET,
        quantity=100,
        stop_loss=97.0,
        target=106.0,
        planned_reward_risk_ratio=2.0,
        pnl=600.0,
    )


def test_format_report_includes_key_figures() -> None:
    result = BacktestResult(
        config=BacktestConfig(initial_capital=100_000.0, risk_config=make_risk_config()),
        trades=[],
        equity_curve=[],
        daily_pnl=[],
        report=make_report(),
    )

    output = format_report(result)

    assert "BACKTEST RESULTS" in output
    assert "100,000.00" in output
    assert "105,000.00" in output
    assert "60.00%" in output
    assert "2.00" in output  # profit factor


def test_format_report_handles_missing_profit_factor_and_sharpe() -> None:
    result = BacktestResult(
        config=BacktestConfig(initial_capital=100_000.0, risk_config=make_risk_config()),
        trades=[],
        equity_curve=[],
        daily_pnl=[],
        report=make_report(profit_factor=None, sharpe_ratio=None),
    )

    output = format_report(result)

    assert "N/A" in output


def test_format_trade_includes_key_fields() -> None:
    line = format_trade(make_trade(), 1)

    assert "#1" in line
    assert "EMABreakout" in line
    assert "Long" in line
    assert "Target" in line
    assert "600.00" in line
