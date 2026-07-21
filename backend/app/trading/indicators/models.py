"""
The single, immutable output of the Indicator Engine.

close_price was added while building Phase 8 (Strategy Engine), not
originally part of Phase 5's approved field list - the EMA Breakout
Strategy's "price above/below EMA" and "price above/below VWAP"
confirmations need the underlying candle close, which the engine already
computes internally but never previously exposed on the output model.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.trading.indicators.open_interest import OpenInterestSignal
from app.trading.indicators.trend_direction import TrendDirection
from app.trading.indicators.volume_analysis import VolumeSignal


class IndicatorSnapshot(BaseModel):
    model_config = ConfigDict(frozen=True)

    as_of: datetime

    close_price: float

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
