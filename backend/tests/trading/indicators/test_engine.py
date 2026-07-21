import pytest
from pydantic import ValidationError

from app.trading.indicators.engine import calculate_indicator_snapshot
from app.trading.indicators.models import IndicatorSnapshot
from app.trading.indicators.open_interest import OpenInterestSignal
from app.trading.indicators.trend_direction import TrendDirection
from tests.trading.indicators.helpers import make_candles


def test_calculate_indicator_snapshot_assembles_all_indicators() -> None:
    rows = []
    price = 100.0
    for _ in range(25):
        rows.append((price, price + 1, price - 1, price, 100))
        price += 2.0
    candles = make_candles(rows)

    snapshot = calculate_indicator_snapshot(
        candles,
        total_call_oi=120_000,
        total_put_oi=180_000,
        price_change=5.0,
        oi_change=10.0,
    )

    assert isinstance(snapshot, IndicatorSnapshot)
    assert snapshot.put_call_ratio == 1.5
    assert snapshot.open_interest_signal == OpenInterestSignal.LONG_BUILDUP
    assert snapshot.trend_direction == TrendDirection.UPTREND
    assert snapshot.supertrend_is_bullish is True
    assert snapshot.ema > 0
    assert 0 <= snapshot.rsi <= 100
    assert snapshot.vwap > 0


def test_indicator_snapshot_is_immutable() -> None:
    rows = [(100.0, 101.0, 99.0, 100.0, 100) for _ in range(25)]
    candles = make_candles(rows)

    snapshot = calculate_indicator_snapshot(
        candles,
        total_call_oi=100,
        total_put_oi=100,
        price_change=0.0,
        oi_change=0.0,
    )

    with pytest.raises(ValidationError):
        snapshot.ema = 999.0  # type: ignore[misc]
