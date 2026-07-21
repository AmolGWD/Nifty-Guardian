from app.trading.context.models import MomentumContext
from app.trading.context.momentum import classify_momentum
from tests.trading.context.helpers import make_snapshot


def test_strong_momentum_when_rsi_far_above_midpoint() -> None:
    assert classify_momentum(make_snapshot(rsi=75.0)) == MomentumContext.STRONG_MOMENTUM


def test_strong_momentum_when_rsi_far_below_midpoint() -> None:
    assert classify_momentum(make_snapshot(rsi=25.0)) == MomentumContext.STRONG_MOMENTUM


def test_weak_momentum_when_rsi_near_midpoint() -> None:
    assert classify_momentum(make_snapshot(rsi=55.0)) == MomentumContext.WEAK_MOMENTUM


def test_boundary_at_exactly_the_threshold_is_strong() -> None:
    assert classify_momentum(make_snapshot(rsi=70.0)) == MomentumContext.STRONG_MOMENTUM
