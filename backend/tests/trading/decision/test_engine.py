import pytest
from pydantic import ValidationError

from app.trading.conditions.models import NoTradeReason
from app.trading.decision.engine import build_trade_recommendation
from app.trading.decision.models import RecommendationStrength, TradeRecommendation
from app.trading.risk.models import RiskRejectionReason
from app.trading.strategy.models import StrategyDirection, StrategyStrength
from tests.trading.decision.helpers import make_candidate
from tests.trading.strategy.helpers import make_trading_conditions


def test_single_qualifying_candidate_is_recommended() -> None:
    candidate = make_candidate(strategy_name="EMABreakout", direction=StrategyDirection.LONG)

    recommendation = build_trade_recommendation(
        candidates=[candidate], trading_conditions=make_trading_conditions()
    )

    assert isinstance(recommendation, TradeRecommendation)
    assert recommendation.recommended is True
    assert recommendation.direction == StrategyDirection.LONG
    assert recommendation.selected_strategy == "EMABreakout"
    assert recommendation.recommendation_strength == RecommendationStrength.STRONG
    assert recommendation.risk_summary == candidate.risk_assessment


def test_stronger_candidate_is_selected_over_weaker() -> None:
    weaker = make_candidate(strategy_name="Weaker", strength=StrategyStrength.MODERATE)
    stronger = make_candidate(strategy_name="Stronger", strength=StrategyStrength.STRONG)

    recommendation = build_trade_recommendation(
        candidates=[weaker, stronger], trading_conditions=make_trading_conditions()
    )

    assert recommendation.selected_strategy == "Stronger"
    assert recommendation.recommendation_strength == RecommendationStrength.STRONG


def test_ties_are_broken_by_higher_reward_risk_ratio() -> None:
    lower_ratio = make_candidate(strategy_name="LowerRatio", reward_risk_ratio=1.5)
    higher_ratio = make_candidate(strategy_name="HigherRatio", reward_risk_ratio=3.0)

    recommendation = build_trade_recommendation(
        candidates=[lower_ratio, higher_ratio], trading_conditions=make_trading_conditions()
    )

    assert recommendation.selected_strategy == "HigherRatio"


def test_exact_ties_are_broken_by_registration_order() -> None:
    first = make_candidate(strategy_name="First")
    second = make_candidate(strategy_name="Second")

    recommendation = build_trade_recommendation(
        candidates=[first, second], trading_conditions=make_trading_conditions()
    )

    assert recommendation.selected_strategy == "First"


def test_invalid_strategy_is_excluded_even_if_risk_ok() -> None:
    invalid = make_candidate(strategy_name="Invalid", valid=False, strength=StrategyStrength.STRONG)
    valid = make_candidate(strategy_name="Valid", valid=True, strength=StrategyStrength.MODERATE)

    recommendation = build_trade_recommendation(
        candidates=[invalid, valid], trading_conditions=make_trading_conditions()
    )

    assert recommendation.selected_strategy == "Valid"


def test_risk_not_ok_candidate_is_excluded_even_if_strategy_valid() -> None:
    risky = make_candidate(
        strategy_name="Risky",
        risk_ok=False,
        strength=StrategyStrength.STRONG,
        rejection_reasons=[RiskRejectionReason.DAILY_LOSS_LIMIT_EXCEEDED],
    )
    safe = make_candidate(strategy_name="Safe", risk_ok=True, strength=StrategyStrength.MODERATE)

    recommendation = build_trade_recommendation(
        candidates=[risky, safe], trading_conditions=make_trading_conditions()
    )

    assert recommendation.selected_strategy == "Safe"


def test_no_recommendation_when_no_candidate_qualifies() -> None:
    invalid = make_candidate(strategy_name="Invalid", valid=False)
    risky = make_candidate(
        strategy_name="Risky",
        risk_ok=False,
        rejection_reasons=[RiskRejectionReason.MAX_TRADES_PER_DAY_REACHED],
    )

    recommendation = build_trade_recommendation(
        candidates=[invalid, risky], trading_conditions=make_trading_conditions()
    )

    assert recommendation.recommended is False
    assert recommendation.direction == StrategyDirection.NONE
    assert recommendation.selected_strategy is None
    assert recommendation.recommendation_strength is None
    assert recommendation.risk_summary is None
    assert any("Invalid: strategy not valid" in warning for warning in recommendation.warnings)
    assert any("Risky: risk not ok" in warning for warning in recommendation.warnings)


def test_no_recommendation_when_no_candidates_at_all() -> None:
    recommendation = build_trade_recommendation(
        candidates=[], trading_conditions=make_trading_conditions()
    )

    assert recommendation.recommended is False
    assert recommendation.warnings == ["No strategies were evaluated"]


def test_recommended_is_false_when_trading_not_permitted_even_with_a_qualifying_candidate() -> None:
    candidate = make_candidate(strategy_name="EMABreakout")

    recommendation = build_trade_recommendation(
        candidates=[candidate],
        trading_conditions=make_trading_conditions(
            can_trade=False, no_trade_reason=NoTradeReason.SESSION_INVALID
        ),
    )

    assert recommendation.recommended is False
    assert recommendation.direction == StrategyDirection.LONG
    assert recommendation.selected_strategy == "EMABreakout"
    assert recommendation.risk_summary == candidate.risk_assessment
    assert "Trading not permitted: SessionInvalid" in recommendation.warnings


def test_trade_recommendation_is_immutable() -> None:
    recommendation = build_trade_recommendation(
        candidates=[make_candidate()], trading_conditions=make_trading_conditions()
    )

    with pytest.raises(ValidationError):
        recommendation.recommended = False  # type: ignore[misc]
