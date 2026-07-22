import csv
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

from app.market_data.schemas import Candle
from app.trading.backtest.models import BacktestConfig
from app.trading.risk.models import RiskConfig


def build_trending_weekday_candles(
    num_days: int, *, start: datetime = datetime(2026, 1, 5, 9, 15)
) -> list[Candle]:
    """
    Consecutive weekdays only (2026-01-05 is a Monday) - trading
    sessions are invalid on weekends
    (app.trading.conditions.session_validation), so a naive
    day-by-day iteration would silently skip those candles' worth of
    signal. A clear uptrend each day (small pullback every sixth
    candle so RSI settles at a strong but realistic value), so
    EMABreakoutStrategy actually takes trades - matches the pattern in
    tests/trading/backtest/test_backtest_engine.py and
    scripts/demo_pipeline.py.
    """
    candles: list[Candle] = []
    close = 100.0
    day = start

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


def write_candles_csv(candles: list[Candle], path: str | Path) -> None:
    with open(path, "w", newline="", encoding="utf-8") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(["Timestamp", "Open", "High", "Low", "Close", "Volume"])
        for candle in candles:
            writer.writerow(
                [
                    candle.timestamp.isoformat(),
                    candle.open,
                    candle.high,
                    candle.low,
                    candle.close,
                    candle.volume,
                ]
            )


def make_synthetic_dataset(num_days: int = 14) -> str:
    candles = build_trending_weekday_candles(num_days)
    path = Path(tempfile.mkdtemp(prefix="validation-test-")) / "synthetic.csv"
    write_candles_csv(candles, path)
    return str(path)


def make_base_backtest_config() -> BacktestConfig:
    return BacktestConfig(initial_capital=100_000.0, risk_config=RiskConfig(), warmup_candles=20)
