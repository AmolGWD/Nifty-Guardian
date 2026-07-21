import pytest

from app.trading.indicators.vwap import calculate_vwap
from tests.trading.indicators.helpers import make_candles


def test_vwap_matches_hand_calculated_value() -> None:
    # candle1: tp=(10+8+9)/3=9.0, vol=100 -> pv=900
    # candle2: tp=(12+10+11)/3=11.0, vol=200 -> pv=2200
    # vwap = (900+2200)/(100+200) = 3100/300 = 10.3333...
    candles = make_candles(
        [
            (9, 10, 8, 9, 100),
            (11, 12, 10, 11, 200),
        ]
    )

    assert calculate_vwap(candles) == pytest.approx(10.3333, abs=1e-4)


def test_vwap_single_candle_equals_its_own_typical_price() -> None:
    candles = make_candles([(9, 12, 6, 9, 50)])

    # typical price = (12+6+9)/3 = 9.0
    assert calculate_vwap(candles) == 9.0


def test_vwap_raises_on_empty_input() -> None:
    with pytest.raises(ValueError, match="at least 1 candle"):
        calculate_vwap([])
