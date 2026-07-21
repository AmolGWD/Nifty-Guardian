"""
Combines every candidate strategy's evaluation and risk assessment,
plus TradingConditions, into one TradeRecommendation. Does not execute
trades, maintain positions, or update P&L - it only determines whether
a recommendation exists and explains why.

A candidate "qualifies" when its StrategyEvaluation is valid AND its
RiskAssessment is risk_ok - both gates are independent (Phases 8/9),
and this is the first layer allowed to combine them. Among qualifying
candidates, the strongest wins (Strong over Moderate - Weak never
qualifies, since Phase 8's `valid` already requires at least Moderate),
tie-broken by the higher reward/risk ratio, then by registration order
- fully deterministic, no randomness.

TradingConditions.can_trade is a final, separate gate on `recommended`
itself: even the best qualifying candidate is only actionable when
trading is currently permitted. Mirroring the transparency pattern from
Phases 7-9, the technical read (direction, selected_strategy,
risk_summary) is still reported when `can_trade` is False, with a
warning citing `no_trade_reason` - only `recommended` reflects that it
isn't actionable.
"""

from app.trading.conditions.models import TradingConditions
from app.trading.decision.models import (
    RecommendationStrength,
    StrategyCandidate,
    TradeRecommendation,
)
from app.trading.strategy.models import StrategyDirection, StrategyStrength

_STRENGTH_RANK = {
    StrategyStrength.WEAK: 0,
    StrategyStrength.MODERATE: 1,
    StrategyStrength.STRONG: 2,
}


def build_trade_recommendation(
    *,
    candidates: list[StrategyCandidate],
    trading_conditions: TradingConditions,
) -> TradeRecommendation:
    qualifying = [
        candidate
        for candidate in candidates
        if candidate.evaluation.valid and candidate.risk_assessment.risk_ok
    ]

    if not qualifying:
        return TradeRecommendation(
            recommended=False,
            direction=StrategyDirection.NONE,
            selected_strategy=None,
            recommendation_strength=None,
            reasons=[],
            warnings=_no_qualifying_candidate_warnings(candidates, trading_conditions),
            risk_summary=None,
        )

    best = _select_best(qualifying)

    warnings = list(best.evaluation.warnings)
    if not trading_conditions.can_trade:
        warnings.append(f"Trading not permitted: {trading_conditions.no_trade_reason}")

    return TradeRecommendation(
        recommended=trading_conditions.can_trade,
        direction=best.evaluation.direction,
        selected_strategy=best.evaluation.strategy_name,
        recommendation_strength=RecommendationStrength(best.evaluation.strength.value),
        reasons=list(best.evaluation.reasons),
        warnings=warnings,
        risk_summary=best.risk_assessment,
    )


def _select_best(qualifying: list[StrategyCandidate]) -> StrategyCandidate:
    return max(
        qualifying,
        key=lambda candidate: (
            _STRENGTH_RANK[candidate.evaluation.strength],
            candidate.risk_assessment.reward_risk_ratio,
        ),
    )


def _no_qualifying_candidate_warnings(
    candidates: list[StrategyCandidate], trading_conditions: TradingConditions
) -> list[str]:
    warnings: list[str] = []

    if not trading_conditions.can_trade:
        warnings.append(f"Trading not permitted: {trading_conditions.no_trade_reason}")

    if not candidates:
        warnings.append("No strategies were evaluated")
        return warnings

    for candidate in candidates:
        name = candidate.evaluation.strategy_name
        if not candidate.evaluation.valid:
            warnings.append(f"{name}: strategy not valid")
        if not candidate.risk_assessment.risk_ok:
            reasons = ", ".join(candidate.risk_assessment.rejection_reasons)
            warnings.append(f"{name}: risk not ok ({reasons})")

    return warnings
