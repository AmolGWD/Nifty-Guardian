import pytest

from app.signals.confidence_engine import compute_guardian_score, compute_reward_risk_ratio
from app.trading.strategy.models import StrategyStrength
from tests.signals.helpers import make_evaluation


def test_reward_risk_ratio_basic() -> None:
    ratio = compute_reward_risk_ratio(entry_price=100.0, stop_loss=95.0, target=115.0)
    assert ratio == pytest.approx(3.0)


def test_reward_risk_ratio_zero_risk_returns_zero() -> None:
    assert compute_reward_risk_ratio(entry_price=100.0, stop_loss=100.0, target=115.0) == 0.0


def test_guardian_score_strong_with_full_credit_rr() -> None:
    evaluation = make_evaluation(strength=StrategyStrength.STRONG)
    score = compute_guardian_score(evaluation, entry_price=100.0, stop_loss=95.0, target=115.0)

    assert score.strength == StrategyStrength.STRONG
    assert score.reward_risk_ratio == pytest.approx(3.0)
    assert score.score == pytest.approx(100.0)  # 70 base + full 30 bonus


def test_guardian_score_weak_with_poor_rr() -> None:
    evaluation = make_evaluation(strength=StrategyStrength.WEAK)
    score = compute_guardian_score(evaluation, entry_price=100.0, stop_loss=95.0, target=100.0)

    assert score.reward_risk_ratio == 0.0
    assert score.score == pytest.approx(35.0)  # weak base, zero rr bonus


def test_guardian_score_moderate_with_partial_rr() -> None:
    evaluation = make_evaluation(strength=StrategyStrength.MODERATE)
    score = compute_guardian_score(evaluation, entry_price=100.0, stop_loss=95.0, target=107.5)

    # rr = 1.5, bonus_ratio = 1.5/3 = 0.5 -> bonus = 15
    assert score.score == pytest.approx(70.0)


def test_guardian_score_caps_at_100_even_with_excess_rr() -> None:
    evaluation = make_evaluation(strength=StrategyStrength.STRONG)
    score = compute_guardian_score(evaluation, entry_price=100.0, stop_loss=95.0, target=200.0)

    assert score.score == 100.0


def test_guardian_score_reasons_are_reused_from_evaluation() -> None:
    evaluation = make_evaluation(reasons=["custom reason one", "custom reason two"])
    score = compute_guardian_score(evaluation, entry_price=100.0, stop_loss=95.0, target=115.0)

    assert score.reasons == ["custom reason one", "custom reason two"]
