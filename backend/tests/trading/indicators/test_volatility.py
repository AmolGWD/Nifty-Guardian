import pytest

from app.trading.indicators.volatility import calculate_atr, calculate_atr_percent
from tests.trading.indicators.helpers import make_candles

# true ranges, period=3:
#  c0 (h=12,l=8,c=10): first candle -> tr = 12-8 = 4
#  c1 (h=14,l=9,c=13), prev_close=10: tr = max(5, |14-10|=4, |9-10|=1) = 5
#  c2 (h=15,l=11,c=12), prev_close=13: tr = max(4, |15-13|=2, |11-13|=2) = 4
#  c3 (h=16,l=13,c=15), prev_close=12: tr = max(3, |16-12|=4, |13-12|=1) = 4
# seed atr = (4+5+4)/3 = 13/3
# next atr = (13/3*2 + 4)/3 = 38/9 = 4.222222...
_CANDLES = make_candles(
    [
        (10, 12, 8, 10, 100),
        (13, 14, 9, 13, 100),
        (12, 15, 11, 12, 100),
        (15, 16, 13, 15, 100),
    ]
)


def test_atr_matches_hand_calculated_value() -> None:
    assert calculate_atr(_CANDLES, period=3) == pytest.approx(4.2222, abs=1e-4)


def test_atr_percent_matches_hand_calculated_value() -> None:
    # 4.222222 / 15 * 100 = 28.148148...
    assert calculate_atr_percent(_CANDLES, period=3) == pytest.approx(28.1481, abs=1e-4)


def test_atr_raises_with_insufficient_candles() -> None:
    with pytest.raises(ValueError, match="Need at least"):
        calculate_atr(_CANDLES[:2], period=3)
