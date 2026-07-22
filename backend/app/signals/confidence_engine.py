"""
Guardian Score: a single, explainable 0-100 number computed from
already-frozen data - `StrategyEvaluation.strength` (Phase 8) and the
reward:risk ratio implied by a filled `Order`'s own stop-loss/target
(Phase 19) - never a new indicator, never a new strategy rule.

Formula, deliberately simple and fully documented (no hidden weights):

    base(strength)  = Strong: 70, Moderate: 55, Weak: 35
    rr_bonus         = min(reward_risk_ratio / 3.0, 1.0) * 30
    score            = min(base + rr_bonus, 100.0)

A reward:risk ratio of 3:1 or better contributes the full 30-point
bonus; anything lower scales down linearly. This rewards trades that
are both technically strong (many agreeing checks) AND well-priced
(a favorable risk:reward), without ever re-deciding direction or
validity - those are exclusively the Strategy/Risk/Decision Engines'
job, already done by the time this function is called.
"""

from app.signals.models import GuardianScore
from app.trading.strategy.models import StrategyEvaluation, StrategyStrength

_BASE_SCORE_BY_STRENGTH: dict[StrategyStrength, float] = {
    StrategyStrength.STRONG: 70.0,
    StrategyStrength.MODERATE: 55.0,
    StrategyStrength.WEAK: 35.0,
}

_FULL_CREDIT_REWARD_RISK_RATIO = 3.0
_REWARD_RISK_BONUS_POINTS = 30.0


def compute_reward_risk_ratio(*, entry_price: float, stop_loss: float, target: float) -> float:
    risk = abs(entry_price - stop_loss)
    reward = abs(target - entry_price)
    if risk == 0:
        return 0.0
    return round(reward / risk, 4)


def compute_guardian_score(
    evaluation: StrategyEvaluation, *, entry_price: float, stop_loss: float, target: float
) -> GuardianScore:
    reward_risk_ratio = compute_reward_risk_ratio(
        entry_price=entry_price, stop_loss=stop_loss, target=target
    )
    base = _BASE_SCORE_BY_STRENGTH[evaluation.strength]
    bonus_ratio = min(reward_risk_ratio / _FULL_CREDIT_REWARD_RISK_RATIO, 1.0)
    score = min(base + bonus_ratio * _REWARD_RISK_BONUS_POINTS, 100.0)
    return GuardianScore(
        score=round(score, 2),
        strength=evaluation.strength,
        reward_risk_ratio=reward_risk_ratio,
        reasons=list(evaluation.reasons),
    )
