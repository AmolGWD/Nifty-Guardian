import pytest

from app.market_data.schemas import Candle
from app.trading.indicators.supertrend import calculate_supertrend
from tests.trading.indicators.helpers import make_candles


def _rising_candles(n: int = 15) -> list[Candle]:
    rows = []
    price = 100.0
    for _ in range(n):
        rows.append((price, price + 1, price - 1, price, 100))
        price += 2.0
    return make_candles(rows)


def _falling_candles(n: int = 15) -> list[Candle]:
    rows = []
    price = 200.0
    for _ in range(n):
        rows.append((price, price + 1, price - 1, price, 100))
        price -= 2.0
    return make_candles(rows)


def test_supertrend_is_bullish_in_a_clear_uptrend() -> None:
    candles = _rising_candles()

    result = calculate_supertrend(candles, period=3, multiplier=3.0)

    assert result.is_bullish is True
    # In an uptrend the SuperTrend line trails below price.
    assert result.value < candles[-1].close


def test_supertrend_is_bearish_in_a_clear_downtrend() -> None:
    candles = _falling_candles()

    result = calculate_supertrend(candles, period=3, multiplier=3.0)

    assert result.is_bullish is False
    # In a downtrend the SuperTrend line trails above price.
    assert result.value > candles[-1].close


def test_supertrend_raises_with_insufficient_candles() -> None:
    candles = _rising_candles(n=3)

    with pytest.raises(ValueError, match="Need more than"):
        calculate_supertrend(candles, period=3)
