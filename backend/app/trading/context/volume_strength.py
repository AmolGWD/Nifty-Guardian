"""
Volume Strength context - a direct relabeling of the Indicator Engine's
own volume_signal classification.
"""

from app.trading.context.models import VolumeStrengthContext
from app.trading.indicators.models import IndicatorSnapshot
from app.trading.indicators.volume_analysis import VolumeSignal

_MAPPING = {
    VolumeSignal.ABOVE_AVERAGE: VolumeStrengthContext.STRONG_VOLUME,
    VolumeSignal.BELOW_AVERAGE: VolumeStrengthContext.WEAK_VOLUME,
    VolumeSignal.AVERAGE: VolumeStrengthContext.AVERAGE_VOLUME,
}


def classify_volume_strength(snapshot: IndicatorSnapshot) -> VolumeStrengthContext:
    return _MAPPING[snapshot.volume_signal]
