"""
Formats a complete AnalyticsReport for console display - presentation
only, every figure is read directly from the AnalyticsReport (and the
BacktestResult's equity curve, for the ASCII charts), never
recalculated here.
"""

from app.trading.analytics.charts import (
    render_drawdown_curve,
    render_equity_curve,
    render_monthly_returns,
    render_trade_distribution,
)
from app.trading.analytics.models import AnalyticsReport
from app.trading.backtest.models import BacktestResult

_BANNER = "=" * 33


def _fmt(value: float | None, suffix: str = "") -> str:
    return f"{value:,.2f}{suffix}" if value is not None else "N/A"


def _header(title: str) -> list[str]:
    return [_BANNER, title, _BANNER]


def format_analytics_report(analytics: AnalyticsReport, result: BacktestResult) -> str:
    sections = [
        _format_overall(analytics),
        _format_yearly(analytics),
        _format_monthly(analytics),
        _format_regimes(analytics),
        _format_time_analysis(analytics),
        _format_trade_distribution(analytics),
        _format_risk_analysis(analytics),
        _format_strategies(analytics),
        _format_charts(analytics, result),
    ]
    return "\n\n".join(sections)


def _format_overall(analytics: AnalyticsReport) -> str:
    o = analytics.overall
    lines = _header("OVERALL PERFORMANCE") + [
        f"Initial Capital:    {o.initial_capital:,.2f}",
        f"Final Capital:      {o.final_capital:,.2f}",
        f"CAGR:               {_fmt(o.cagr, '%')}",
        f"Annual Return:      {_fmt(o.annual_return, '%')}",
        f"Net Profit:         {o.net_profit:,.2f}",
        f"Total Return:       {o.total_return_percent:.2f}%",
        f"Total Trades:       {o.total_trades}",
        f"Winning Trades:     {o.winning_trades}",
        f"Losing Trades:      {o.losing_trades}",
        f"Win Rate:           {o.win_rate:.2f}%",
        f"Profit Factor:      {_fmt(o.profit_factor)}",
        f"Expectancy:         {o.expectancy:,.2f}",
        f"Average Win:        {o.average_win:,.2f}",
        f"Average Loss:       {o.average_loss:,.2f}",
        f"Largest Win:        {o.largest_win:,.2f}",
        f"Largest Loss:       {o.largest_loss:,.2f}",
        f"Reward:Risk:        {o.reward_risk:.2f}",
        f"Sharpe Ratio:       {_fmt(o.sharpe_ratio)}",
        f"Sortino Ratio:      {_fmt(o.sortino_ratio)}",
        f"Calmar Ratio:       {_fmt(o.calmar_ratio)}",
        f"Recovery Factor:    {_fmt(o.recovery_factor)}",
        f"Maximum Drawdown:   {o.max_drawdown:,.2f}",
    ]
    return "\n".join(lines)


def _format_yearly(analytics: AnalyticsReport) -> str:
    lines = _header("YEARLY PERFORMANCE")
    if not analytics.yearly:
        lines.append("(no data)")
        return "\n".join(lines)

    header = f"{'Year':<6}{'Trades':>8}{'Win %':>10}{'Net Profit':>14}"
    header += f"{'Return %':>10}{'Max DD':>12}"
    lines.append(header)
    for year in analytics.yearly:
        lines.append(
            f"{year.year:<6}{year.trades:>8}{year.win_rate:>9.2f}%"
            f"{year.net_profit:>14,.2f}{year.return_percent:>9.2f}%{year.max_drawdown:>12,.2f}"
        )
    return "\n".join(lines)


def _format_monthly(analytics: AnalyticsReport) -> str:
    lines = _header("MONTHLY PERFORMANCE")
    if not analytics.monthly:
        lines.append("(no data)")
        return "\n".join(lines)

    lines.append(f"{'Month':<10}{'Trades':>8}{'Win %':>10}{'Net PnL':>14}{'Return %':>10}")
    for month in analytics.monthly:
        lines.append(
            f"{month.year}-{month.month:02d}  {month.trade_count:>6}"
            f"{month.win_rate:>9.2f}%{month.net_pnl:>14,.2f}{month.return_percent:>9.2f}%"
        )
    return "\n".join(lines)


def _format_regimes(analytics: AnalyticsReport) -> str:
    regimes = analytics.market_regimes
    lines = _header("MARKET REGIME ANALYSIS")

    for title, buckets in (
        ("Trend", regimes.by_trend),
        ("Volatility", regimes.by_volatility),
        ("Momentum", regimes.by_momentum),
    ):
        lines.append(f"-- {title} --")
        if not buckets:
            lines.append("  (no data)")
            continue
        for bucket in buckets:
            lines.append(
                f"  {bucket.regime:<16} trades={bucket.trade_count:<4} "
                f"win_rate={bucket.win_rate:6.2f}%  net_pnl={bucket.net_pnl:,.2f}"
            )
    return "\n".join(lines)


def _format_time_analysis(analytics: AnalyticsReport) -> str:
    t = analytics.time_analysis
    lines = _header("TIME ANALYSIS")
    lines.append(f"Best Hour:    {t.best_hour or 'N/A'}")
    lines.append(f"Worst Hour:   {t.worst_hour or 'N/A'}")
    lines.append(f"Best Weekday: {t.best_weekday or 'N/A'}")
    lines.append(f"Worst Weekday: {t.worst_weekday or 'N/A'}")

    for title, buckets in (
        ("By Hour", t.by_hour),
        ("By Weekday", t.by_weekday),
        ("By Session", t.by_session),
        ("By Expiry", t.by_expiry),
    ):
        lines.append(f"-- {title} --")
        if not buckets:
            lines.append("  (no data)")
            continue
        for bucket in buckets:
            lines.append(
                f"  {bucket.label:<12} trades={bucket.trade_count:<4} "
                f"win_rate={bucket.win_rate:6.2f}%  net_pnl={bucket.net_pnl:,.2f}"
            )
    return "\n".join(lines)


def _format_trade_distribution(analytics: AnalyticsReport) -> str:
    d = analytics.trade_distribution
    lines = _header("TRADE DISTRIBUTION")
    lines.append(f"Average Holding Time: {d.average_holding_minutes:.1f} min")
    lines.append(f"Median Holding Time:  {d.median_holding_minutes:.1f} min")
    lines.append(f"Longest Holding Time: {d.longest_holding_minutes:.1f} min")
    lines.append(f"Shortest Holding Time:{d.shortest_holding_minutes:.1f} min")
    lines.append(f"Stop Loss %:          {d.stop_loss_percent:.2f}%")
    lines.append(f"Target %:             {d.target_percent:.2f}%")
    lines.append(f"End Of Day %:         {d.end_of_day_percent:.2f}%")
    return "\n".join(lines)


def _format_risk_analysis(analytics: AnalyticsReport) -> str:
    r = analytics.risk_analysis
    lines = _header("RISK ANALYSIS")
    lines.append(f"Longest Winning Streak:  {r.longest_winning_streak}")
    lines.append(f"Longest Losing Streak:   {r.longest_losing_streak}")
    lines.append(f"Average Winning Streak:  {r.average_winning_streak:.2f}")
    lines.append(f"Average Losing Streak:   {r.average_losing_streak:.2f}")
    lines.append(f"Largest Equity Peak:     {r.largest_equity_peak:,.2f}")
    lines.append(f"Largest Equity Valley:   {r.largest_equity_valley:,.2f}")
    lines.append(f"Drawdown Episodes:       {len(r.drawdown_episodes)}")
    for episode in r.drawdown_episodes[:5]:
        recovery = episode.recovery_time if episode.recovery_time is not None else "ongoing"
        lines.append(
            f"  peak={episode.peak_time} trough={episode.trough_time} "
            f"recovery={recovery} depth={episode.depth:,.2f} ({episode.depth_percent:.2f}%)"
        )
    return "\n".join(lines)


def _format_strategies(analytics: AnalyticsReport) -> str:
    lines = _header("STRATEGY BREAKDOWN")
    if not analytics.strategies:
        lines.append("(no data)")
        return "\n".join(lines)

    for strategy in analytics.strategies:
        lines.append(
            f"{strategy.strategy_name:<16} trades={strategy.trade_count:<4} "
            f"win_rate={strategy.win_rate:6.2f}%  net_pnl={strategy.net_pnl:,.2f}  "
            f"profit_factor={_fmt(strategy.profit_factor)}"
        )
    return "\n".join(lines)


def _format_charts(analytics: AnalyticsReport, result: BacktestResult) -> str:
    lines = _header("EQUITY CURVE")
    lines.append(render_equity_curve(result.equity_curve))
    lines.append("")
    lines.extend(_header("DRAWDOWN CURVE"))
    lines.append(render_drawdown_curve(result.equity_curve))
    lines.append("")
    lines.extend(_header("MONTHLY RETURNS"))
    lines.append(render_monthly_returns(analytics.monthly))
    lines.append("")
    lines.extend(_header("TRADE DISTRIBUTION CHART"))
    lines.append(render_trade_distribution(analytics.trade_distribution))
    return "\n".join(lines)
