import pytest

from app.trading.indicators.volume_analysis import VolumeSignal, analyze_volume
from tests.trading.indicators.helpers import make_candles


def test_above_average_when_latest_volume_spikes() -> None:
    # average = (100+100+100+300)/4 = 150, ratio = 300/150 = 2.0
    candles = make_candles(
        [
            (10, 10, 10, 10, 100),
            (10, 10, 10, 10, 100),
            (10, 10, 10, 10, 100),
            (10, 10, 10, 10, 300),
        ]
    )

    result = analyze_volume(candles)

    assert result.average_volume == 150.0
    assert result.ratio == 2.0
    assert result.signal == VolumeSignal.ABOVE_AVERAGE


def test_below_average_when_latest_volume_dries_up() -> None:
    # average = (100+100+100+20)/4 = 80, ratio = 20/80 = 0.25
    candles = make_candles(
        [
            (10, 10, 10, 10, 100),
            (10, 10, 10, 10, 100),
            (10, 10, 10, 10, 100),
            (10, 10, 10, 10, 20),
        ]
    )

    result = analyze_volume(candles)

    assert result.ratio == 0.25
    assert result.signal == VolumeSignal.BELOW_AVERAGE


def test_average_when_ratio_is_near_one() -> None:
    candles = make_candles([(10, 10, 10, 10, 100) for _ in range(4)])

    result = analyze_volume(candles)

    assert result.ratio == 1.0
    assert result.signal == VolumeSignal.AVERAGE


def test_raises_on_empty_input() -> None:
    with pytest.raises(ValueError, match="at least 1 candle"):
        analyze_volume([])
