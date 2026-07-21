"""
Composes the independent indicator calculators into one IndicatorSnapshot.

This is the only place in app.trading.indicators that calls more than
one calculator - each calculator itself never depends on another; this
module just runs all of them and assembles the result.
"""

from datetime import datetime

from app.market_data.schemas import Candle
from app.trading.indicators.ema import calculate_ema
from app.trading.indicators.models import IndicatorSnapshot
from app.trading.indicators.open_interest import analyze_open_interest
from app.trading.indicators.put_call_ratio import calculate_put_call_ratio
from app.trading.indicators.rsi import calculate_rsi
from app.trading.indicators.supertrend import calculate_supertrend
from app.trading.indicators.trend_direction import determine_trend
from app.trading.indicators.volatility import calculate_atr, calculate_atr_percent
from app.trading.indicators.volume_analysis import analyze_volume
from app.trading.indicators.vwap import calculate_vwap


def calculate_indicator_snapshot(
    candles: list[Candle],
    *,
    total_call_oi: int,
    total_put_oi: int,
    price_change: float,
    oi_change: float,
    ema_period: int = 20,
    rsi_period: int = 14,
    supertrend_period: int = 10,
    supertrend_multiplier: float = 3.0,
    atr_period: int = 14,
) -> IndicatorSnapshot:
    supertrend = calculate_supertrend(
        candles, period=supertrend_period, multiplier=supertrend_multiplier
    )
    volume = analyze_volume(candles)

    return IndicatorSnapshot(
        as_of=datetime.now(),
        ema=calculate_ema(candles, period=ema_period),
        rsi=calculate_rsi(candles, period=rsi_period),
        vwap=calculate_vwap(candles),
        supertrend_value=supertrend.value,
        supertrend_is_bullish=supertrend.is_bullish,
        atr=calculate_atr(candles, period=atr_period),
        atr_percent=calculate_atr_percent(candles, period=atr_period),
        put_call_ratio=calculate_put_call_ratio(total_put_oi, total_call_oi),
        open_interest_signal=analyze_open_interest(price_change, oi_change),
        trend_direction=determine_trend(candles),
        volume_average=volume.average_volume,
        volume_ratio=volume.ratio,
        volume_signal=volume.signal,
    )
