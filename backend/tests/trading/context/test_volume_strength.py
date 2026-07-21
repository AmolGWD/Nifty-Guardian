from app.trading.context.models import VolumeStrengthContext
from app.trading.context.volume_strength import classify_volume_strength
from app.trading.indicators.volume_analysis import VolumeSignal
from tests.trading.context.helpers import make_snapshot


def test_above_average_maps_to_strong() -> None:
    snapshot = make_snapshot(volume_signal=VolumeSignal.ABOVE_AVERAGE)
    assert classify_volume_strength(snapshot) == VolumeStrengthContext.STRONG_VOLUME


def test_below_average_maps_to_weak() -> None:
    snapshot = make_snapshot(volume_signal=VolumeSignal.BELOW_AVERAGE)
    assert classify_volume_strength(snapshot) == VolumeStrengthContext.WEAK_VOLUME


def test_average_maps_to_average() -> None:
    snapshot = make_snapshot(volume_signal=VolumeSignal.AVERAGE)
    assert classify_volume_strength(snapshot) == VolumeStrengthContext.AVERAGE_VOLUME
