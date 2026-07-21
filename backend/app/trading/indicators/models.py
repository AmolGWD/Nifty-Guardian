"""
The single, immutable output of the Indicator Engine.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.trading.indicators.open_interest import OpenInterestSignal
from app.trading.indicators.trend_direction import TrendDirection
from app.trading.indicators.volume_analysis import VolumeSignal


class IndicatorSnapshot(BaseModel):
    model_config = ConfigDict(frozen=True)

    as_of: datetime

    ema: float
    rsi: float
    vwap: float

    supertrend_value: float
    supertrend_is_bullish: bool

    atr: float
    atr_percent: float

    put_call_ratio: float
    open_interest_signal: OpenInterestSignal

    trend_direction: TrendDirection

    volume_average: float
    volume_ratio: float
    volume_signal: VolumeSignal
