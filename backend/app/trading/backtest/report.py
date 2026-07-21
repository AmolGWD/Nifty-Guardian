"""
Formats a BacktestResult for console display. Presentation only - all
figures here are read directly from PerformanceReport/BacktestTrade,
never recomputed.
"""

from app.trading.backtest.models import BacktestResult, BacktestTrade


def format_report(result: BacktestResult) -> str:
    report = result.report
    profit_factor = (
        f"{report.profit_factor:.2f}" if report.profit_factor is not None else "N/A"
    )
    sharpe_ratio = f"{report.sharpe_ratio:.2f}" if report.sharpe_ratio is not None else "N/A"

    lines = [
        "=================================",
        "BACKTEST RESULTS",
        "=================================",
        f"Initial Capital:      {report.initial_capital:,.2f}",
        f"Final Capital:        {report.final_capital:,.2f}",
        f"Net Profit:           {report.net_profit:,.2f}",
        "",
        f"Total Trades:         {report.total_trades}",
        f"Winning Trades:       {report.winning_trades}",
        f"Losing Trades:        {report.losing_trades}",
        f"Win Rate:             {report.win_rate:.2f}%",
        "",
        f"Average Win:          {report.average_win:,.2f}",
        f"Average Loss:         {report.average_loss:,.2f}",
        f"Largest Win:          {report.largest_win:,.2f}",
        f"Largest Loss:         {report.largest_loss:,.2f}",
        "",
        f"Profit Factor:        {profit_factor}",
        f"Expectancy:           {report.expectancy:,.2f}",
        f"Average Reward:Risk:  {report.average_reward_risk_ratio:.2f}",
        f"Max Drawdown:         {report.max_drawdown:,.2f}",
        f"Max Consecutive Wins: {report.max_consecutive_wins}",
        f"Max Consecutive Loss: {report.max_consecutive_losses}",
        f"Sharpe Ratio:         {sharpe_ratio}",
        "=================================",
    ]

    return "\n".join(lines)


def format_trade(trade: BacktestTrade, index: int) -> str:
    return (
        f"#{index} {trade.strategy_name} {trade.direction.value} "
        f"entry={trade.entry_price:.2f}@{trade.entry_time} "
        f"exit={trade.exit_price:.2f}@{trade.exit_time} "
        f"({trade.exit_reason.value}) qty={trade.quantity} pnl={trade.pnl:,.2f}"
    )
