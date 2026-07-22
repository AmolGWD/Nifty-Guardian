from datetime import datetime, timedelta

from app.market_data.schemas import Candle
from app.trading.backtest.backtest_engine import run_backtest
from app.trading.backtest.models import BacktestResult, BacktestTrade, ExitReason
from app.trading.strategy.models import StrategyDirection
from tests.trading.backtest.helpers import make_backtest_config


def build_multi_day_uptrend_candles(num_days: int = 4) -> list[Candle]:
    """Consecutive weekdays, a clear uptrend each day (see tests/trading/backtest's own fixture)."""
    candles: list[Candle] = []
    close = 100.0
    day = datetime(2026, 1, 5, 9, 15)  # a Monday

    while len(candles) < num_days * 25:
        if day.isoweekday() in (6, 7):
            day += timedelta(days=1)
            continue

        timestamp = day
        for i in range(25):
            open_price = close
            close = close - 1.0 if i % 6 == 5 else close + 2.5
            high = max(open_price, close) + 1.0
            low = min(open_price, close) - 1.0
            volume = 10_000 + (i * 500)
            candles.append(
                Candle(
                    timestamp=timestamp, open=open_price, high=high, low=low, close=close,
                    volume=volume,
                )
            )
            timestamp += timedelta(minutes=15)
        day += timedelta(days=1)

    return candles


def make_real_backtest_result(num_days: int = 4) -> tuple[BacktestResult, list[Candle]]:
    candles = build_multi_day_uptrend_candles(num_days)
    config = make_backtest_config()
    result = run_backtest(candles, config)
    return result, candles


def make_trade(
    *,
    entry_time: datetime = datetime(2026, 1, 5, 9, 30),
    entry_price: float = 100.0,
    exit_time: datetime = datetime(2026, 1, 5, 11, 0),
    exit_price: float = 105.0,
    quantity: int = 10,
    direction: StrategyDirection = StrategyDirection.LONG,
) -> BacktestTrade:
    sign = -1 if direction == StrategyDirection.SHORT else 1
    pnl = round((exit_price - entry_price) * quantity * sign, 4)
    return BacktestTrade(
        strategy_name="EMABreakout",
        direction=direction,
        entry_time=entry_time,
        entry_price=entry_price,
        exit_time=exit_time,
        exit_price=exit_price,
        exit_reason=ExitReason.TARGET,
        quantity=quantity,
        stop_loss=entry_price - 5.0,
        target=exit_price,
        planned_reward_risk_ratio=1.0,
        pnl=pnl,
    )
