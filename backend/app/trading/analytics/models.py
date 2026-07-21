"""
Analytics domain models - every section of an AnalyticsReport, frozen,
same discipline as the rest of the trading domain (ADR-0006).

AnalyticsConfig has no required fields - every default is a genuinely
optional refinement (session-window widths, an optional expiry-date
set), not a placeholder for something this package can't function
without. `expiry_dates` defaults to empty: the CSV backtests this
analyzes carry no options-expiry concept (same gap already flagged in
`app.trading.backtest.models.BacktestConfig` for OI data) - callers
analyzing an options-aware backtest can supply the real set without
any change to this package.
"""

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict

from app.trading.strategy.models import StrategyDirection


class AnalyticsConfig(BaseModel):
    model_config = ConfigDict(frozen=True)

    opening_session_minutes: int = 30
    closing_session_minutes: int = 30
    expiry_dates: frozenset[date] = frozenset()


class OverallPerformance(BaseModel):
    model_config = ConfigDict(frozen=True)

    initial_capital: float
    final_capital: float

    cagr: float | None
    annual_return: float | None
    net_profit: float
    total_return_percent: float

    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float

    profit_factor: float | None
    expectancy: float
    average_win: float
    average_loss: float
    largest_win: float
    largest_loss: float
    reward_risk: float

    sharpe_ratio: float | None
    sortino_ratio: float | None
    calmar_ratio: float | None
    recovery_factor: float | None
    max_drawdown: float


class YearlyPerformance(BaseModel):
    model_config = ConfigDict(frozen=True)

    year: int
    trades: int
    win_rate: float
    net_profit: float
    return_percent: float
    max_drawdown: float


class MonthlyPerformance(BaseModel):
    model_config = ConfigDict(frozen=True)

    year: int
    month: int
    trade_count: int
    win_rate: float
    net_pnl: float
    return_percent: float


class RegimeBucket(BaseModel):
    model_config = ConfigDict(frozen=True)

    regime: str
    trade_count: int
    win_rate: float
    net_pnl: float


class MarketRegimeAnalysis(BaseModel):
    model_config = ConfigDict(frozen=True)

    by_trend: list[RegimeBucket]
    by_volatility: list[RegimeBucket]
    by_momentum: list[RegimeBucket]


class TimeBucket(BaseModel):
    model_config = ConfigDict(frozen=True)

    label: str
    trade_count: int
    win_rate: float
    net_pnl: float


class TimeAnalysis(BaseModel):
    model_config = ConfigDict(frozen=True)

    by_hour: list[TimeBucket]
    by_weekday: list[TimeBucket]
    by_session: list[TimeBucket]
    by_expiry: list[TimeBucket]

    best_hour: str | None
    worst_hour: str | None
    best_weekday: str | None
    worst_weekday: str | None


class DirectionBucket(BaseModel):
    model_config = ConfigDict(frozen=True)

    direction: StrategyDirection
    trade_count: int
    win_rate: float
    net_pnl: float


class ExitReasonBucket(BaseModel):
    model_config = ConfigDict(frozen=True)

    exit_reason: str
    trade_count: int
    percentage: float


class TradeDistribution(BaseModel):
    model_config = ConfigDict(frozen=True)

    average_holding_minutes: float
    median_holding_minutes: float
    longest_holding_minutes: float
    shortest_holding_minutes: float

    by_direction: list[DirectionBucket]
    by_exit_reason: list[ExitReasonBucket]

    stop_loss_percent: float
    target_percent: float
    end_of_day_percent: float


class DrawdownEpisode(BaseModel):
    model_config = ConfigDict(frozen=True)

    peak_time: datetime
    trough_time: datetime
    recovery_time: datetime | None
    depth: float
    depth_percent: float


class RiskAnalysis(BaseModel):
    model_config = ConfigDict(frozen=True)

    longest_winning_streak: int
    longest_losing_streak: int
    average_winning_streak: float
    average_losing_streak: float

    drawdown_episodes: list[DrawdownEpisode]

    largest_equity_peak: float
    largest_equity_valley: float


class StrategyPerformance(BaseModel):
    model_config = ConfigDict(frozen=True)

    strategy_name: str
    trade_count: int
    win_rate: float
    net_pnl: float
    profit_factor: float | None


class AnalyticsReport(BaseModel):
    model_config = ConfigDict(frozen=True)

    overall: OverallPerformance
    yearly: list[YearlyPerformance]
    monthly: list[MonthlyPerformance]
    market_regimes: MarketRegimeAnalysis
    time_analysis: TimeAnalysis
    trade_distribution: TradeDistribution
    risk_analysis: RiskAnalysis
    strategies: list[StrategyPerformance]
