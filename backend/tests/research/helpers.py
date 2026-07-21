from pathlib import Path

from app.data.models import Timeframe
from app.research.experiment import create_experiment
from app.research.models import Experiment, ExperimentResult, ExperimentStatus, ParameterValue
from app.trading.analytics.analytics_engine import build_analytics_report
from app.trading.analytics.models import (
    AnalyticsReport,
    MarketRegimeAnalysis,
    OverallPerformance,
    RiskAnalysis,
    TimeAnalysis,
    TradeDistribution,
)
from app.trading.backtest.backtest_engine import run_backtest
from app.trading.backtest.loader import load_candles_from_csv
from app.trading.backtest.models import BacktestConfig
from app.trading.risk.models import RiskConfig

SAMPLE_CSV = Path(__file__).parent / "fixtures" / "sample_candles.csv"


def make_backtest_config(
    *,
    initial_capital: float = 100_000.0,
    risk_per_trade_percent: float = 1.0,
    stop_loss_atr_multiplier: float = 1.5,
    target_atr_multiplier: float = 3.0,
    warmup_candles: int = 20,
) -> BacktestConfig:
    return BacktestConfig(
        initial_capital=initial_capital,
        risk_config=RiskConfig(
            risk_per_trade_percent=risk_per_trade_percent,
            stop_loss_atr_multiplier=stop_loss_atr_multiplier,
            target_atr_multiplier=target_atr_multiplier,
            max_daily_loss=5_000.0,
            max_trades_per_day=5,
            max_concurrent_positions=1,
            max_capital_exposure_percent=100.0,
        ),
        warmup_candles=warmup_candles,
    )


def make_test_experiment(
    *,
    name: str = "Test Experiment",
    dataset_path: str | Path = SAMPLE_CSV,
    parameters: dict[str, ParameterValue] | None = None,
    backtest_config: BacktestConfig | None = None,
    tags: list[str] | None = None,
) -> Experiment:
    return create_experiment(
        name=name,
        description="A test experiment",
        strategy="EMABreakout",
        dataset_path=str(dataset_path),
        backtest_config=backtest_config if backtest_config is not None else make_backtest_config(),
        timeframe=Timeframe.FIFTEEN_MINUTE,
        parameters=parameters,
        tags=tags,
        capture_git_commit=False,
    )


def make_test_result(
    *,
    experiment: Experiment | None = None,
    status: ExperimentStatus = ExperimentStatus.COMPLETED,
) -> ExperimentResult:
    experiment = experiment if experiment is not None else make_test_experiment()
    candles = load_candles_from_csv(experiment.dataset_path)
    backtest_result = run_backtest(candles, experiment.backtest_config)
    analytics_report = build_analytics_report(backtest_result, candles)

    return ExperimentResult(
        experiment=experiment,
        status=status,
        duration_seconds=0.1,
        backtest_result=backtest_result,
        analytics_report=analytics_report,
        error=None,
    )


def make_synthetic_result(
    *,
    name: str = "Synthetic",
    net_profit: float = 1_000.0,
    profit_factor: float | None = 2.0,
    expectancy: float = 100.0,
    max_drawdown: float = 500.0,
    recovery_factor: float | None = 2.0,
    sharpe_ratio: float | None = 1.5,
    calmar_ratio: float | None = 1.2,
    win_rate: float = 55.0,
    status: ExperimentStatus = ExperimentStatus.COMPLETED,
) -> ExperimentResult:
    """
    Builds an ExperimentResult with a fully-controlled OverallPerformance
    but without running a real backtest - fast and exact for
    comparison/ranking/scoring tests that only care about
    `overall.*` figures.
    """
    experiment = make_test_experiment(name=name)

    overall = OverallPerformance(
        initial_capital=100_000.0,
        final_capital=100_000.0 + net_profit,
        cagr=None,
        annual_return=None,
        net_profit=net_profit,
        total_return_percent=net_profit / 100_000.0 * 100,
        total_trades=10,
        winning_trades=6,
        losing_trades=4,
        win_rate=win_rate,
        profit_factor=profit_factor,
        expectancy=expectancy,
        average_win=200.0,
        average_loss=-100.0,
        largest_win=400.0,
        largest_loss=-200.0,
        reward_risk=2.0,
        sharpe_ratio=sharpe_ratio,
        sortino_ratio=None,
        calmar_ratio=calmar_ratio,
        recovery_factor=recovery_factor,
        max_drawdown=max_drawdown,
    )

    analytics_report = AnalyticsReport(
        overall=overall,
        yearly=[],
        monthly=[],
        market_regimes=MarketRegimeAnalysis(by_trend=[], by_volatility=[], by_momentum=[]),
        time_analysis=TimeAnalysis(
            by_hour=[], by_weekday=[], by_session=[], by_expiry=[],
            best_hour=None, worst_hour=None, best_weekday=None, worst_weekday=None,
        ),
        trade_distribution=TradeDistribution(
            average_holding_minutes=0.0, median_holding_minutes=0.0,
            longest_holding_minutes=0.0, shortest_holding_minutes=0.0,
            by_direction=[], by_exit_reason=[],
            stop_loss_percent=0.0, target_percent=0.0, end_of_day_percent=0.0,
        ),
        risk_analysis=RiskAnalysis(
            longest_winning_streak=0, longest_losing_streak=0,
            average_winning_streak=0.0, average_losing_streak=0.0,
            drawdown_episodes=[], largest_equity_peak=0.0, largest_equity_valley=0.0,
        ),
        strategies=[],
    )

    return ExperimentResult(
        experiment=experiment,
        status=status,
        duration_seconds=0.1,
        backtest_result=None,
        analytics_report=analytics_report if status == ExperimentStatus.COMPLETED else None,
        error=None if status == ExperimentStatus.COMPLETED else "synthetic failure",
    )
