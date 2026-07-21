import pytest
from pydantic import ValidationError

from app.config.strategy_config import StrategyParameters
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


def test_explicit_default_parameters_reproduce_the_no_argument_construction() -> None:
    """Phase 15: default config must equal the previous hardcoded behavior."""
    snapshot = make_snapshot(
        close_price=110.0, ema=100.0, rsi=60.0, vwap=100.0, supertrend_is_bullish=True
    )
    context = make_market_context().model_copy(update={"trend": TrendContext.BULLISH_TREND})
    conditions = make_trading_conditions()

    default_evaluation = EMABreakoutStrategy().evaluate(snapshot, context, conditions)
    explicit_evaluation = EMABreakoutStrategy(StrategyParameters()).evaluate(
        snapshot, context, conditions
    )

    assert default_evaluation == explicit_evaluation


def test_changing_rsi_threshold_changes_the_confirmation_direction() -> None:
    """RSI of 52 is inconclusive under the default 55/45 thresholds..."""
    snapshot = make_snapshot(rsi=52.0)
    context = make_market_context()
    conditions = make_trading_conditions()

    default_evaluation = EMABreakoutStrategy().evaluate(snapshot, context, conditions)
    assert "RSI confirmation: RSI 52.00 inconclusive" in (
        default_evaluation.reasons + default_evaluation.warnings
    )

    # ...but is a bullish confirmation once the bullish threshold is lowered to 50.
    lowered_threshold_strategy = EMABreakoutStrategy(
        StrategyParameters(rsi_bullish_threshold=50.0)
    )
    evaluation = lowered_threshold_strategy.evaluate(snapshot, context, conditions)
    assert "RSI confirmation: RSI 52.00 above 50" in (evaluation.reasons + evaluation.warnings)


def test_disabling_vwap_and_supertrend_reduces_the_check_count() -> None:
    snapshot = make_snapshot(
        close_price=110.0, ema=100.0, rsi=60.0, vwap=100.0, supertrend_is_bullish=True
    )
    context = make_market_context().model_copy(update={"trend": TrendContext.BULLISH_TREND})
    conditions = make_trading_conditions()

    strategy = EMABreakoutStrategy(
        StrategyParameters(vwap_enabled=False, supertrend_enabled=False, min_agreeing_checks=3)
    )
    evaluation = strategy.evaluate(snapshot, context, conditions)

    # only ema_alignment, rsi_confirmation, trend_agreement remain (3 checks, not 5).
    assert len(evaluation.reasons) + len(evaluation.warnings) == 3
    assert evaluation.strength == StrategyStrength.STRONG
    assert evaluation.valid is True


def test_raising_min_agreeing_checks_makes_a_previously_valid_evaluation_invalid() -> None:
    snapshot = make_snapshot(
        close_price=110.0, ema=100.0, rsi=50.0, vwap=100.0, supertrend_is_bullish=True
    )
    context = make_market_context().model_copy(update={"trend": TrendContext.BULLISH_TREND})
    conditions = make_trading_conditions()

    stricter_strategy = EMABreakoutStrategy(StrategyParameters(min_agreeing_checks=5))
    evaluation = stricter_strategy.evaluate(snapshot, context, conditions)

    assert evaluation.direction == StrategyDirection.LONG
    assert evaluation.strength == StrategyStrength.MODERATE
    assert evaluation.valid is False
