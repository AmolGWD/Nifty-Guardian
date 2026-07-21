from datetime import datetime, timedelta

from app.market_data.schemas import Candle
from app.trading.backtest.models import BacktestConfig
from app.trading.risk.models import RiskConfig


def make_backtest_candles(
    rows: list[tuple[float, float, float, float, int]],
    *,
    start: datetime = datetime(2026, 7, 21, 9, 15),
    interval_minutes: int = 15,
) -> list[Candle]:
    """
    rows: list of (open, high, low, close, volume) tuples, oldest
    first. Defaults to a Tuesday starting at market open, at the same
    15-minute cadence used elsewhere in this test suite.
    """
    timestamp = start
    candles = []
    for row in rows:
        candles.append(
            Candle(
                timestamp=timestamp,
                open=row[0],
                high=row[1],
                low=row[2],
                close=row[3],
                volume=row[4],
            )
        )
        timestamp += timedelta(minutes=interval_minutes)
    return candles


def make_risk_config(
    *,
    risk_per_trade_percent: float = 1.0,
    stop_loss_atr_multiplier: float = 1.5,
    target_atr_multiplier: float = 3.0,
    max_daily_loss: float = 5_000.0,
    max_trades_per_day: int = 5,
    max_concurrent_positions: int = 1,
    max_capital_exposure_percent: float = 100.0,
) -> RiskConfig:
    return RiskConfig(
        risk_per_trade_percent=risk_per_trade_percent,
        stop_loss_atr_multiplier=stop_loss_atr_multiplier,
        target_atr_multiplier=target_atr_multiplier,
        max_daily_loss=max_daily_loss,
        max_trades_per_day=max_trades_per_day,
        max_concurrent_positions=max_concurrent_positions,
        max_capital_exposure_percent=max_capital_exposure_percent,
    )


def make_backtest_config(
    *,
    initial_capital: float = 100_000.0,
    risk_config: RiskConfig | None = None,
    warmup_candles: int = 20,
) -> BacktestConfig:
    return BacktestConfig(
        initial_capital=initial_capital,
        risk_config=risk_config if risk_config is not None else make_risk_config(),
        warmup_candles=warmup_candles,
    )
