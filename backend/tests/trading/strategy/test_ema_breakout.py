import pytest
from pydantic import ValidationError

from app.trading.conditions.models import NoTradeReason
from app.trading.context.models import TrendContext
from app.trading.strategy.ema_breakout import EMABreakoutStrategy
from app.trading.strategy.models import StrategyDirection, StrategyEvaluation, StrategyStrength
from tests.trading.conditions.helpers import make_market_context
from tests.trading.context.helpers import make_snapshot
from tests.trading.strategy.helpers import make_trading_conditions


def test_all_five_checks_agree_bullish() -> None:
    snapshot = make_snapshot(
        close_price=110.0, ema=100.0, rsi=60.0, vwap=100.0, supertrend_is_bullish=True
    )
    context = make_market_context().model_copy(update={"trend": TrendContext.BULLISH_TREND})
    conditions = make_trading_conditions()

    evaluation = EMABreakoutStrategy().evaluate(snapshot, context, conditions)

    assert isinstance(evaluation, StrategyEvaluation)
    assert evaluation.strategy_name == "EMABreakout"
    assert evaluation.direction == StrategyDirection.LONG
    assert evaluation.strength == StrategyStrength.STRONG
    assert evaluation.valid is True
    assert len(evaluation.reasons) == 5
    assert evaluation.warnings == []


def test_all_five_checks_agree_bearish() -> None:
    snapshot = make_snapshot(
        close_price=90.0, ema=100.0, rsi=40.0, vwap=100.0, supertrend_is_bullish=False
    )
    context = make_market_context().model_copy(update={"trend": TrendContext.BEARISH_TREND})
    conditions = make_trading_conditions()

    evaluation = EMABreakoutStrategy().evaluate(snapshot, context, conditions)

    assert evaluation.direction == StrategyDirection.SHORT
    assert evaluation.strength == StrategyStrength.STRONG
    assert evaluation.valid is True
    assert len(evaluation.reasons) == 5
    assert evaluation.warnings == []


def test_four_of_five_checks_agree_is_moderate_and_valid() -> None:
    snapshot = make_snapshot(
        close_price=110.0, ema=100.0, rsi=50.0, vwap=100.0, supertrend_is_bullish=True
    )
    context = make_market_context().model_copy(update={"trend": TrendContext.BULLISH_TREND})
    conditions = make_trading_conditions()

    evaluation = EMABreakoutStrategy().evaluate(snapshot, context, conditions)

    assert evaluation.direction == StrategyDirection.LONG
    assert evaluation.strength == StrategyStrength.MODERATE
    assert evaluation.valid is True
    assert len(evaluation.reasons) == 4
    assert len(evaluation.warnings) == 1


def test_three_of_five_checks_agree_is_weak_and_invalid() -> None:
    snapshot = make_snapshot(
        close_price=110.0, ema=100.0, rsi=50.0, vwap=100.0, supertrend_is_bullish=True
    )
    context = make_market_context()  # default trend is SIDEWAYS_TREND -> neutral
    conditions = make_trading_conditions()

    evaluation = EMABreakoutStrategy().evaluate(snapshot, context, conditions)

    assert evaluation.direction == StrategyDirection.LONG
    assert evaluation.strength == StrategyStrength.WEAK
    assert evaluation.valid is False


def test_evenly_split_checks_produce_no_direction() -> None:
    snapshot = make_snapshot(
        close_price=110.0, ema=100.0, rsi=40.0, vwap=120.0, supertrend_is_bullish=True
    )
    context = make_market_context()  # default trend is SIDEWAYS_TREND -> neutral
    conditions = make_trading_conditions()

    evaluation = EMABreakoutStrategy().evaluate(snapshot, context, conditions)

    assert evaluation.direction == StrategyDirection.NONE
    assert evaluation.valid is False


def test_valid_is_false_when_trading_conditions_block_trading_even_with_full_alignment() -> None:
    snapshot = make_snapshot(
        close_price=110.0, ema=100.0, rsi=60.0, vwap=100.0, supertrend_is_bullish=True
    )
    context = make_market_context().model_copy(update={"trend": TrendContext.BULLISH_TREND})
    conditions = make_trading_conditions(
        can_trade=False, no_trade_reason=NoTradeReason.SESSION_INVALID
    )

    evaluation = EMABreakoutStrategy().evaluate(snapshot, context, conditions)

    assert evaluation.direction == StrategyDirection.LONG
    assert evaluation.strength == StrategyStrength.STRONG
    assert evaluation.valid is False
    assert "Trading not permitted: SessionInvalid" in evaluation.warnings


def test_strategy_evaluation_is_immutable() -> None:
    snapshot = make_snapshot()
    context = make_market_context()
    conditions = make_trading_conditions()

    evaluation = EMABreakoutStrategy().evaluate(snapshot, context, conditions)

    with pytest.raises(ValidationError):
        evaluation.valid = False  # type: ignore[misc]
