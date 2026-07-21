import pytest
from pydantic import ValidationError

from app.market_data.market_session import MarketSessionStatus
from app.trading.context.engine import build_market_context
from app.trading.context.models import Bias, MarketContext, OverallMarketState, TrendContext
from app.trading.indicators.trend_direction import TrendDirection
from tests.trading.context.helpers import make_snapshot


def test_build_market_context_assembles_all_dimensions() -> None:
    snapshot = make_snapshot(
        trend_direction=TrendDirection.UPTREND,
        supertrend_is_bullish=True,
        rsi=75.0,
        atr_percent=0.8,
        put_call_ratio=1.5,
    )

    context = build_market_context(snapshot, MarketSessionStatus.OPEN)

    assert isinstance(context, MarketContext)
    assert context.trend == TrendContext.BULLISH_TREND
    assert context.market_bias == Bias.BULLISH_BIAS
    assert context.session_state == MarketSessionStatus.OPEN
    assert context.overall_state == OverallMarketState.STRONG_BULLISH


def test_market_context_is_immutable() -> None:
    context = build_market_context(make_snapshot(), MarketSessionStatus.CLOSED)

    with pytest.raises(ValidationError):
        context.trend = TrendContext.BEARISH_TREND  # type: ignore[misc]
