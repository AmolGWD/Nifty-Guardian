from app.trading.context.models import VolatilityContext
from app.trading.context.volatility import classify_volatility
from tests.trading.context.helpers import make_snapshot


def test_high_volatility_above_threshold() -> None:
    assert classify_volatility(make_snapshot(atr_percent=1.0)) == VolatilityContext.HIGH_VOLATILITY


def test_low_volatility_below_threshold() -> None:
    assert classify_volatility(make_snapshot(atr_percent=0.1)) == VolatilityContext.LOW_VOLATILITY


def test_boundary_at_exactly_the_threshold_is_high() -> None:
    assert classify_volatility(make_snapshot(atr_percent=0.5)) == VolatilityContext.HIGH_VOLATILITY
