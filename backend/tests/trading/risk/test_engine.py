import pytest
from pydantic import ValidationError

from app.trading.risk.engine import build_risk_assessment
from app.trading.risk.models import RiskAssessment, RiskRejectionReason
from app.trading.strategy.models import StrategyDirection
from tests.trading.risk.helpers import (
    make_capital_state,
    make_risk_config,
    make_strategy_evaluation,
)


def test_full_assessment_matches_hand_calculated_values_when_long() -> None:
    assessment = build_risk_assessment(
        strategy_evaluation=make_strategy_evaluation(direction=StrategyDirection.LONG),
        entry_price=100.0,
        atr=2.0,
        config=make_risk_config(),
        capital_state=make_capital_state(),
    )

    assert isinstance(assessment, RiskAssessment)
    assert assessment.stop_loss == 97.0
    assert assessment.target == 106.0
    assert assessment.reward_risk_ratio == 2.0
    assert assessment.position_size == 333
    assert assessment.capital_required == 33_300.0
    assert assessment.risk_ok is True
    assert assessment.rejection_reasons == []


def test_stop_loss_and_target_flip_sides_when_short() -> None:
    assessment = build_risk_assessment(
        strategy_evaluation=make_strategy_evaluation(direction=StrategyDirection.SHORT),
        entry_price=100.0,
        atr=2.0,
        config=make_risk_config(),
        capital_state=make_capital_state(),
    )

    assert assessment.stop_loss == 103.0
    assert assessment.target == 94.0
    assert assessment.risk_ok is True


def test_no_direction_collapses_stop_loss_and_target_to_entry_price() -> None:
    assessment = build_risk_assessment(
        strategy_evaluation=make_strategy_evaluation(direction=StrategyDirection.NONE),
        entry_price=100.0,
        atr=2.0,
        config=make_risk_config(),
        capital_state=make_capital_state(),
    )

    assert assessment.stop_loss == 100.0
    assert assessment.target == 100.0
    assert assessment.position_size == 0
    assert assessment.capital_required == 0.0
    assert assessment.risk_ok is True
    assert assessment.rejection_reasons == []


def test_rejects_when_daily_loss_limit_exceeded() -> None:
    assessment = build_risk_assessment(
        strategy_evaluation=make_strategy_evaluation(),
        entry_price=100.0,
        atr=2.0,
        config=make_risk_config(max_daily_loss=5000.0),
        capital_state=make_capital_state(realized_loss_today=6000.0),
    )

    assert assessment.risk_ok is False
    assert RiskRejectionReason.DAILY_LOSS_LIMIT_EXCEEDED in assessment.rejection_reasons


def test_rejects_when_max_trades_per_day_reached() -> None:
    assessment = build_risk_assessment(
        strategy_evaluation=make_strategy_evaluation(),
        entry_price=100.0,
        atr=2.0,
        config=make_risk_config(max_trades_per_day=5),
        capital_state=make_capital_state(trades_taken_today=5),
    )

    assert assessment.risk_ok is False
    assert RiskRejectionReason.MAX_TRADES_PER_DAY_REACHED in assessment.rejection_reasons


def test_rejects_when_capital_exposure_exceeded() -> None:
    assessment = build_risk_assessment(
        strategy_evaluation=make_strategy_evaluation(),
        entry_price=100.0,
        atr=2.0,
        config=make_risk_config(max_capital_exposure_percent=10.0),
        capital_state=make_capital_state(capital_deployed=9_000.0),
    )

    assert assessment.risk_ok is False
    assert RiskRejectionReason.CAPITAL_EXPOSURE_EXCEEDED in assessment.rejection_reasons


def test_rejects_when_max_concurrent_positions_reached() -> None:
    assessment = build_risk_assessment(
        strategy_evaluation=make_strategy_evaluation(),
        entry_price=100.0,
        atr=2.0,
        config=make_risk_config(max_concurrent_positions=1),
        capital_state=make_capital_state(open_positions=1),
    )

    assert assessment.risk_ok is False
    assert RiskRejectionReason.MAX_CONCURRENT_POSITIONS_REACHED in assessment.rejection_reasons


def test_rejects_when_position_size_rounds_to_zero() -> None:
    assessment = build_risk_assessment(
        strategy_evaluation=make_strategy_evaluation(direction=StrategyDirection.LONG),
        entry_price=100.0,
        atr=2.0,
        config=make_risk_config(),
        capital_state=make_capital_state(total_capital=100.0),
    )

    assert assessment.position_size == 0
    assert assessment.risk_ok is False
    assert RiskRejectionReason.POSITION_SIZE_TOO_SMALL in assessment.rejection_reasons


def test_risk_assessment_ignores_strategy_validity() -> None:
    invalid_assessment = build_risk_assessment(
        strategy_evaluation=make_strategy_evaluation(valid=False),
        entry_price=100.0,
        atr=2.0,
        config=make_risk_config(),
        capital_state=make_capital_state(),
    )
    valid_assessment = build_risk_assessment(
        strategy_evaluation=make_strategy_evaluation(valid=True),
        entry_price=100.0,
        atr=2.0,
        config=make_risk_config(),
        capital_state=make_capital_state(),
    )

    assert invalid_assessment.risk_ok == valid_assessment.risk_ok
    assert invalid_assessment.stop_loss == valid_assessment.stop_loss
    assert invalid_assessment.position_size == valid_assessment.position_size


def test_risk_assessment_is_immutable() -> None:
    assessment = build_risk_assessment(
        strategy_evaluation=make_strategy_evaluation(),
        entry_price=100.0,
        atr=2.0,
        config=make_risk_config(),
        capital_state=make_capital_state(),
    )

    with pytest.raises(ValidationError):
        assessment.risk_ok = False  # type: ignore[misc]
