"""
Volume Analysis - compares the latest candle's volume to the average
volume across the given window.
"""

from enum import StrEnum

from pydantic import BaseModel, ConfigDict

from app.market_data.schemas import Candle

_ABOVE_AVERAGE_THRESHOLD = 1.5
_BELOW_AVERAGE_THRESHOLD = 0.5


class VolumeSignal(StrEnum):
    ABOVE_AVERAGE = "ABOVE_AVERAGE"
    BELOW_AVERAGE = "BELOW_AVERAGE"
    AVERAGE = "AVERAGE"


class VolumeAnalysis(BaseModel):
    model_config = ConfigDict(frozen=True)

    average_volume: float
    latest_volume: int
    ratio: float
    signal: VolumeSignal


def analyze_volume(candles: list[Candle]) -> VolumeAnalysis:
    if not candles:
        raise ValueError("Need at least 1 candle to analyze volume")

    volumes = [c.volume for c in candles]
    average_volume = sum(volumes) / len(volumes)
    latest_volume = volumes[-1]

    ratio = latest_volume / average_volume if average_volume > 0 else 0.0

    if ratio >= _ABOVE_AVERAGE_THRESHOLD:
        signal = VolumeSignal.ABOVE_AVERAGE
    elif ratio <= _BELOW_AVERAGE_THRESHOLD:
        signal = VolumeSignal.BELOW_AVERAGE
    else:
        signal = VolumeSignal.AVERAGE

    return VolumeAnalysis(
        average_volume=round(average_volume, 4),
        latest_volume=latest_volume,
        ratio=round(ratio, 4),
        signal=signal,
    )
