from datetime import datetime
from pathlib import Path

from app.market_data.schemas import Candle
from app.trading.backtest.loader import load_candles_from_csv

_FIXTURE_PATH = Path(__file__).parent / "fixtures" / "sample_candles.csv"


def test_load_candles_from_csv_parses_all_rows() -> None:
    candles = load_candles_from_csv(_FIXTURE_PATH)

    assert len(candles) == 3
    assert all(isinstance(candle, Candle) for candle in candles)


def test_load_candles_from_csv_parses_values_correctly() -> None:
    candles = load_candles_from_csv(_FIXTURE_PATH)

    first = candles[0]
    assert first.timestamp == datetime(2026, 7, 21, 9, 15)
    assert first.open == 100.0
    assert first.high == 101.5
    assert first.low == 99.5
    assert first.close == 101.0
    assert first.volume == 10000


def test_load_candles_from_csv_preserves_row_order() -> None:
    candles = load_candles_from_csv(_FIXTURE_PATH)

    assert [candle.close for candle in candles] == [101.0, 102.5, 103.5]
