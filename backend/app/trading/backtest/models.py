"""
Backtesting domain models - trade history, equity curve, daily P&L,
run configuration, and the final performance report. Every model here
is a frozen Pydantic model, same discipline as the rest of
`app.trading` (ADR-0006).

`BacktestConfig` carries `total_call_oi`/`total_put_oi`/`price_change`/
`oi_change` with neutral defaults (call/put OI both 1, so PCR == 1.0;
price/OI change both 0.0, so the Open Interest signal is NEUTRAL) -
the CSV format this phase supports (Timestamp/Open/High/Low/Close/
Volume) carries no option-chain data, so there is no real basis for a
directional PCR/OI read. This mirrors the same gap already flagged in
Phase 5 ("sourcing real OI data is later work"), not a new one -
callers with a richer data source can override these to feed a real
signal without any change to this package.

Phase 16 (Grid Search Strategy Optimization Engine) added
`strategy_parameters` and `ema_period` - both `None`/the existing
hardcoded default, so every pre-Phase-16 `BacktestConfig(...)` call site
is unaffected. Before this, there was no way for anything (not even the
already-existing `StrategyParameters` injection point on
`EMABreakoutStrategy` itself, added Phase 15) to reach an actual
backtest run - `run_backtest()` always built `default_registry()` with
no override, and never passed an `ema_period` through to
`calculate_indicator_snapshot()` at all. This was a genuine, CTO-
authorized narrow exception to this package's freeze (explicitly
requested for Phase 16, not a unilateral gap-fix) - see
`docs/OPTIMIZATION_GUIDE.md`.
"""

from datetime import date, datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict

from app.config.strategy_config import StrategyParameters
from app.trading.risk.models import RiskConfig
from app.trading.strategy.models import StrategyDirection


class ExitReason(StrEnum):
    STOP_LOSS = "StopLoss"
    TARGET = "Target"
    END_OF_DAY = "EndOfDay"
    END_OF_DATA = "EndOfData"


class BacktestTrade(BaseModel):
    model_config = ConfigDict(frozen=True)

    strategy_name: str
    direction: StrategyDirection

    entry_time: datetime
    entry_price: float

    exit_time: datetime
    exit_price: float
    exit_reason: ExitReason

    quantity: int
    stop_loss: float
    target: float
    planned_reward_risk_ratio: float

    pnl: float


class EquityPoint(BaseModel):
    model_config = ConfigDict(frozen=True)

    timestamp: datetime
    equity: float


class DailyPnL(BaseModel):
    model_config = ConfigDict(frozen=True)

    date: date
    pnl: float


class BacktestConfig(BaseModel):
    model_config = ConfigDict(frozen=True)

    initial_capital: float
    risk_config: RiskConfig

    market_open: str = "09:15"
    market_close: str = "15:30"
    opening_range_minutes: int = 15
    no_trade_zone_minutes: int = 15
    cooldown_minutes: int = 5
    min_volume: int = 0

    total_call_oi: int = 1
    total_put_oi: int = 1
    price_change: float = 0.0
    oi_change: float = 0.0

    warmup_candles: int = 20

    # Phase 16: None reproduces exactly the previous, hardcoded behavior
    # (EMABreakoutStrategy() with default StrategyParameters, ema_period=20).
    strategy_parameters: StrategyParameters | None = None
    ema_period: int = 20


class PerformanceReport(BaseModel):
    model_config = ConfigDict(frozen=True)

    initial_capital: float
    final_capital: float
    net_profit: float

    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float

    average_win: float
    average_loss: float
    largest_win: float
    largest_loss: float

    profit_factor: float | None
    expectancy: float
    average_reward_risk_ratio: float

    max_drawdown: float
    max_consecutive_wins: int
    max_consecutive_losses: int

    sharpe_ratio: float | None


class BacktestResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    config: BacktestConfig
    trades: list[BacktestTrade]
    equity_curve: list[EquityPoint]
    daily_pnl: list[DailyPnL]
    report: PerformanceReport
