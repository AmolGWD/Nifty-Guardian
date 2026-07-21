from datetime import datetime

from app.trading.backtest.models import (
    BacktestConfig,
    BacktestTrade,
    EquityPoint,
    ExitReason,
)
from app.trading.risk.models import RiskConfig
from app.trading.strategy.models import StrategyDirection


def make_trade(
    *,
    strategy_name: str = "EMABreakout",
    direction: StrategyDirection = StrategyDirection.LONG,
    entry_time: datetime = datetime(2026, 7, 21, 10, 0),
    entry_price: float = 100.0,
    exit_time: datetime = datetime(2026, 7, 21, 11, 0),
    exit_price: float = 106.0,
    exit_reason: ExitReason = ExitReason.TARGET,
    quantity: int = 100,
    stop_loss: float = 97.0,
    target: float = 106.0,
    planned_reward_risk_ratio: float = 2.0,
    pnl: float = 600.0,
) -> BacktestTrade:
    return BacktestTrade(
        strategy_name=strategy_name,
        direction=direction,
        entry_time=entry_time,
        entry_price=entry_price,
        exit_time=exit_time,
        exit_price=exit_price,
        exit_reason=exit_reason,
        quantity=quantity,
        stop_loss=stop_loss,
        target=target,
        planned_reward_risk_ratio=planned_reward_risk_ratio,
        pnl=pnl,
    )


def make_equity_point(
    *, timestamp: datetime = datetime(2026, 7, 21, 10, 0), equity: float = 100_000.0
) -> EquityPoint:
    return EquityPoint(timestamp=timestamp, equity=equity)


def make_backtest_config(
    *,
    initial_capital: float = 100_000.0,
    warmup_candles: int = 20,
) -> BacktestConfig:
    return BacktestConfig(
        initial_capital=initial_capital,
        risk_config=RiskConfig(
            risk_per_trade_percent=1.0,
            stop_loss_atr_multiplier=1.5,
            target_atr_multiplier=3.0,
            max_daily_loss=5_000.0,
            max_trades_per_day=5,
            max_concurrent_positions=1,
            max_capital_exposure_percent=100.0,
        ),
        warmup_candles=warmup_candles,
    )
