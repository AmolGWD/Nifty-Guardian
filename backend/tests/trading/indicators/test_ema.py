import pytest

from app.trading.indicators.ema import calculate_ema
from tests.trading.indicators.helpers import make_candles


def test_ema_matches_hand_calculated_value() -> None:
    # closes = [10, 11, 12, 13, 14], period=3
    # seed SMA(10,11,12) = 11.0, multiplier = 2/(3+1) = 0.5
    # close=13: ema = (13-11)*0.5+11 = 12.0
    # close=14: ema = (14-12)*0.5+12 = 13.0
    candles = make_candles(
        [
            (10, 10, 10, 10, 100),
            (11, 11, 11, 11, 100),
            (12, 12, 12, 12, 100),
            (13, 13, 13, 13, 100),
            (14, 14, 14, 14, 100),
        ]
    )

    assert calculate_ema(candles, period=3) == 13.0


def test_ema_raises_with_insufficient_candles() -> None:
    candles = make_candles([(10, 10, 10, 10, 100), (11, 11, 11, 11, 100)])

    with pytest.raises(ValueError, match="Need at least"):
        calculate_ema(candles, period=3)


def test_ema_flat_prices_equal_the_price() -> None:
    candles = make_candles([(100, 100, 100, 100, 10) for _ in range(5)])

    assert calculate_ema(candles, period=3) == 100.0
