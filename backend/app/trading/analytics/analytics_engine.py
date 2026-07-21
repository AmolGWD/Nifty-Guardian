"""
Assembles one AnalyticsReport from a completed BacktestResult. Every
figure Phase 11 already computed (Sharpe Ratio, Max Drawdown, win/loss
counts, profit factor, expectancy, average win/loss, reward/risk) is
read directly from `result.report` here, never recalculated - this
module only adds analytics Phase 11 didn't produce (CAGR, Sortino,
Calmar, Recovery Factor, yearly/monthly breakdowns, market regime
buckets, time-of-day buckets, trade distribution, streak/drawdown
detail).

`candles` (the same historical data `run_backtest()` was given) is a
required input alongside `result` - `BacktestResult` alone has no
record of the MarketContext each trade was entered under, so market
regime analysis needs the original candles to recompute it (see
`regime_analysis.py`'s docstring for why).
"""

from app.market_data.schemas import Candle
from app.trading.analytics.equity_analysis import (
    calculate_total_return_percent,
    calculate_years_elapsed,
)
from app.trading.analytics.models import AnalyticsConfig, AnalyticsReport, OverallPerformance
from app.trading.analytics.performance_metrics import (
    calculate_annual_return,
    calculate_cagr,
    calculate_calmar_ratio,
    calculate_recovery_factor,
    calculate_sortino_ratio,
)
from app.trading.analytics.periodic_analysis import (
    analyze_monthly_performance,
    analyze_yearly_performance,
)
from app.trading.analytics.regime_analysis import analyze_market_regimes
from app.trading.analytics.risk_analysis import analyze_risk
from app.trading.analytics.strategy_analysis import analyze_strategies
from app.trading.analytics.time_analysis import analyze_time
from app.trading.analytics.trade_distribution import analyze_trade_distribution
from app.trading.backtest.models import BacktestResult


def _round_or_none(value: float | None) -> float | None:
    return round(value, 4) if value is not None else None


def build_analytics_report(
    result: BacktestResult,
    candles: list[Candle],
    config: AnalyticsConfig | None = None,
) -> AnalyticsReport:
    config = config if config is not None else AnalyticsConfig()
    report = result.report

    years = calculate_years_elapsed(result.equity_curve)
    cagr = calculate_cagr(report.initial_capital, report.final_capital, years)
    annual_return = calculate_annual_return(report.net_profit, report.initial_capital, years)
    sortino_ratio = calculate_sortino_ratio(result.equity_curve)

    max_drawdown_percent = (
        (report.max_drawdown / report.initial_capital * 100) if report.initial_capital else 0.0
    )
    calmar_ratio = calculate_calmar_ratio(cagr, max_drawdown_percent)
    recovery_factor = calculate_recovery_factor(report.net_profit, report.max_drawdown)

    overall = OverallPerformance(
        initial_capital=report.initial_capital,
        final_capital=report.final_capital,
        cagr=_round_or_none(cagr),
        annual_return=_round_or_none(annual_return),
        net_profit=report.net_profit,
        total_return_percent=round(
            calculate_total_return_percent(report.initial_capital, report.final_capital), 4
        ),
        total_trades=report.total_trades,
        winning_trades=report.winning_trades,
        losing_trades=report.losing_trades,
        win_rate=report.win_rate,
        profit_factor=report.profit_factor,
        expectancy=report.expectancy,
        average_win=report.average_win,
        average_loss=report.average_loss,
        largest_win=report.largest_win,
        largest_loss=report.largest_loss,
        reward_risk=report.average_reward_risk_ratio,
        sharpe_ratio=report.sharpe_ratio,
        sortino_ratio=_round_or_none(sortino_ratio),
        calmar_ratio=_round_or_none(calmar_ratio),
        recovery_factor=_round_or_none(recovery_factor),
        max_drawdown=report.max_drawdown,
    )

    return AnalyticsReport(
        overall=overall,
        yearly=analyze_yearly_performance(result.trades, result.equity_curve),
        monthly=analyze_monthly_performance(result.trades, result.equity_curve),
        market_regimes=analyze_market_regimes(result.trades, candles, result.config),
        time_analysis=analyze_time(result.trades, result.config, config),
        trade_distribution=analyze_trade_distribution(result.trades),
        risk_analysis=analyze_risk(result.trades, result.equity_curve),
        strategies=analyze_strategies(result.trades),
    )
