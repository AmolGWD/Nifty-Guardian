from datetime import datetime

from app.trading.indicators.models import IndicatorSnapshot
from app.trading.indicators.open_interest import OpenInterestSignal
from app.trading.indicators.trend_direction import TrendDirection
from app.trading.indicators.volume_analysis import VolumeSignal


def make_snapshot(
    *,
    ema: float = 100.0,
    rsi: float = 50.0,
    vwap: float = 100.0,
    supertrend_value: float = 95.0,
    supertrend_is_bullish: bool = True,
    atr: float = 1.0,
    atr_percent: float = 0.2,
    put_call_ratio: float = 1.0,
    open_interest_signal: OpenInterestSignal = OpenInterestSignal.NEUTRAL,
    trend_direction: TrendDirection = TrendDirection.SIDEWAYS,
    volume_average: float = 100.0,
    volume_ratio: float = 1.0,
    volume_signal: VolumeSignal = VolumeSignal.AVERAGE,
) -> IndicatorSnapshot:
    return IndicatorSnapshot(
        as_of=datetime(2026, 7, 21, 10, 0),
        ema=ema,
        rsi=rsi,
        vwap=vwap,
        supertrend_value=supertrend_value,
        supertrend_is_bullish=supertrend_is_bullish,
        atr=atr,
        atr_percent=atr_percent,
        put_call_ratio=put_call_ratio,
        open_interest_signal=open_interest_signal,
        trend_direction=trend_direction,
        volume_average=volume_average,
        volume_ratio=volume_ratio,
        volume_signal=volume_signal,
    )
