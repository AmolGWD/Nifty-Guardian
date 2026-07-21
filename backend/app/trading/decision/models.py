"""
StrategyCandidate pairs one strategy's evaluation with the risk
assessment computed for its direction - the Decision Engine needs both
together to judge each candidate, since a strategy can be technically
valid while its risk assessment isn't (and vice versa isn't meaningful,
but both are independent per Phases 8/9's own design).

TradeRecommendation is the single, immutable output: whether a
recommendation exists, and why. It does not execute trades, maintain
positions, or update P&L.
"""

from enum import StrEnum

from pydantic import BaseModel, ConfigDict

from app.trading.risk.models import RiskAssessment
from app.trading.strategy.models import StrategyDirection, StrategyEvaluation


class StrategyCandidate(BaseModel):
    model_config = ConfigDict(frozen=True)

    evaluation: StrategyEvaluation
    risk_assessment: RiskAssessment


class RecommendationStrength(StrEnum):
    STRONG = "Strong"
    MODERATE = "Moderate"
    WEAK = "Weak"


class TradeRecommendation(BaseModel):
    model_config = ConfigDict(frozen=True)

    recommended: bool
    direction: StrategyDirection
    selected_strategy: str | None
    recommendation_strength: RecommendationStrength | None

    reasons: list[str]
    warnings: list[str]

    risk_summary: RiskAssessment | None
