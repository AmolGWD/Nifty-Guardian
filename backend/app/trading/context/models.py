"""
The single, immutable output of the Market Context Engine.

Session state reuses app.market_data.market_session.MarketSessionStatus
directly rather than redefining an equivalent enum - it is already a
pure, dependency-free classification, computed by Phase 4 for exactly
this purpose.
"""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict

from app.market_data.market_session import MarketSessionStatus


class TrendContext(StrEnum):
    BULLISH_TREND = "BullishTrend"
    BEARISH_TREND = "BearishTrend"
    SIDEWAYS_TREND = "SidewaysTrend"


class MomentumContext(StrEnum):
    STRONG_MOMENTUM = "StrongMomentum"
    WEAK_MOMENTUM = "WeakMomentum"


class VolatilityContext(StrEnum):
    HIGH_VOLATILITY = "HighVolatility"
    LOW_VOLATILITY = "LowVolatility"


class VolumeStrengthContext(StrEnum):
    STRONG_VOLUME = "StrongVolume"
    WEAK_VOLUME = "WeakVolume"
    AVERAGE_VOLUME = "AverageVolume"


class Bias(StrEnum):
    """Shared by both market_bias and option_chain_bias - both are the
    same bullish/bearish/neutral vocabulary applied to different data."""

    BULLISH_BIAS = "BullishBias"
    BEARISH_BIAS = "BearishBias"
    NEUTRAL_BIAS = "NeutralBias"


class OverallMarketState(StrEnum):
    STRONG_BULLISH = "StrongBullish"
    STRONG_BEARISH = "StrongBearish"
    RANGE_BOUND = "RangeBound"
    VOLATILE_RANGE = "VolatileRange"
    MIXED = "Mixed"


class MarketContext(BaseModel):
    model_config = ConfigDict(frozen=True)

    as_of: datetime

    trend: TrendContext
    momentum: MomentumContext
    volatility: VolatilityContext
    volume_strength: VolumeStrengthContext
    market_bias: Bias
    option_chain_bias: Bias
    session_state: MarketSessionStatus
    overall_state: OverallMarketState
