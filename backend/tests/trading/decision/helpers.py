from app.trading.decision.models import StrategyCandidate
from app.trading.risk.models import RiskAssessment, RiskRejectionReason
from app.trading.strategy.models import StrategyDirection, StrategyEvaluation, StrategyStrength


def make_strategy_evaluation(
    *,
    strategy_name: str = "Test",
    direction: StrategyDirection = StrategyDirection.LONG,
    strength: StrategyStrength = StrategyStrength.STRONG,
    valid: bool = True,
    reasons: list[str] | None = None,
    warnings: list[str] | None = None,
) -> StrategyEvaluation:
    return StrategyEvaluation(
        strategy_name=strategy_name,
        valid=valid,
        direction=direction,
        strength=strength,
        reasons=reasons if reasons is not None else [],
        warnings=warnings if warnings is not None else [],
    )


def make_risk_assessment(
    *,
    risk_ok: bool = True,
    position_size: int = 100,
    stop_loss: float = 97.0,
    target: float = 106.0,
    reward_risk_ratio: float = 2.0,
    capital_required: float = 10_000.0,
    rejection_reasons: list[RiskRejectionReason] | None = None,
) -> RiskAssessment:
    return RiskAssessment(
        risk_ok=risk_ok,
        position_size=position_size,
        stop_loss=stop_loss,
        target=target,
        reward_risk_ratio=reward_risk_ratio,
        capital_required=capital_required,
        rejection_reasons=rejection_reasons if rejection_reasons is not None else [],
    )


def make_candidate(
    *,
    strategy_name: str = "Test",
    direction: StrategyDirection = StrategyDirection.LONG,
    strength: StrategyStrength = StrategyStrength.STRONG,
    valid: bool = True,
    risk_ok: bool = True,
    reward_risk_ratio: float = 2.0,
    rejection_reasons: list[RiskRejectionReason] | None = None,
) -> StrategyCandidate:
    return StrategyCandidate(
        evaluation=make_strategy_evaluation(
            strategy_name=strategy_name, direction=direction, strength=strength, valid=valid
        ),
        risk_assessment=make_risk_assessment(
            risk_ok=risk_ok,
            reward_risk_ratio=reward_risk_ratio,
            rejection_reasons=rejection_reasons,
        ),
    )
