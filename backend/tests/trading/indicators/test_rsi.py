import pytest

from app.trading.indicators.rsi import calculate_rsi
from tests.trading.indicators.helpers import make_candles


def test_rsi_matches_hand_calculated_value() -> None:
    # closes = [10, 11, 12, 11, 13], period=3
    # deltas = [1, 1, -1, 2] -> gains=[1,1,0,2], losses=[0,0,1,0]
    # seed avg_gain=(1+1+0)/3=10/9... computed precisely as fractions:
    # avg_gain=2/3, avg_loss=1/3
    # next step: avg_gain=(2/3*2+2)/3=10/9, avg_loss=(1/3*2+0)/3=2/9
    # rs=(10/9)/(2/9)=5.0 exactly -> rsi=100-100/6=83.3333...
    candles = make_candles(
        [
            (10, 10, 10, 10, 100),
            (11, 11, 11, 11, 100),
            (12, 12, 12, 12, 100),
            (11, 11, 11, 11, 100),
            (13, 13, 13, 13, 100),
        ]
    )

    assert calculate_rsi(candles, period=3) == pytest.approx(83.3333, abs=1e-4)


def test_rsi_is_100_when_no_losses() -> None:
    candles = make_candles(
        [
            (10, 10, 10, 10, 100),
            (11, 11, 11, 11, 100),
            (12, 12, 12, 12, 100),
            (13, 13, 13, 13, 100),
        ]
    )

    assert calculate_rsi(candles, period=3) == 100.0


def test_rsi_raises_with_insufficient_candles() -> None:
    candles = make_candles([(10, 10, 10, 10, 100), (11, 11, 11, 11, 100)])

    with pytest.raises(ValueError, match="Need at least"):
        calculate_rsi(candles, period=3)
