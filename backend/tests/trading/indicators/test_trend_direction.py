import pytest

from app.trading.indicators.trend_direction import TrendDirection, determine_trend
from tests.trading.indicators.helpers import make_candles


def test_uptrend_when_second_half_makes_higher_highs_and_lows() -> None:
    candles = make_candles(
        [
            (10, 12, 8, 11, 100),
            (11, 13, 9, 12, 100),
            (15, 18, 14, 17, 100),
            (17, 20, 16, 19, 100),
        ]
    )

    assert determine_trend(candles) == TrendDirection.UPTREND


def test_downtrend_when_second_half_makes_lower_highs_and_lows() -> None:
    candles = make_candles(
        [
            (17, 20, 16, 19, 100),
            (15, 18, 14, 17, 100),
            (11, 13, 9, 12, 100),
            (10, 12, 8, 11, 100),
        ]
    )

    assert determine_trend(candles) == TrendDirection.DOWNTREND


def test_sideways_when_ranges_overlap() -> None:
    candles = make_candles(
        [
            (10, 15, 8, 12, 100),
            (11, 14, 9, 11, 100),
            (10, 15, 8, 12, 100),
            (11, 14, 9, 11, 100),
        ]
    )

    assert determine_trend(candles) == TrendDirection.SIDEWAYS


def test_raises_with_fewer_than_two_candles() -> None:
    candles = make_candles([(10, 10, 10, 10, 100)])

    with pytest.raises(ValueError, match="at least 2 candles"):
        determine_trend(candles)
