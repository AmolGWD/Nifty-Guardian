from datetime import datetime

from app.market_data.schemas import Candle
from app.paper_trading.event_bus import EventBus
from app.paper_trading.models import Order, OrderStatus
from app.paper_trading.order_manager import OrderManager
from app.trading.risk.models import RiskAssessment, RiskRejectionReason
from app.trading.strategy.models import StrategyDirection, StrategyEvaluation, StrategyStrength


def make_candle(
    *,
    timestamp: datetime = datetime(2026, 1, 5, 9, 30),
    close: float = 100.0,
) -> Candle:
    return Candle(
        timestamp=timestamp, open=close - 1.0, high=close + 1.0, low=close - 1.0,
        close=close, volume=10_000,
    )


def make_strategy_evaluation(
    *,
    direction: StrategyDirection = StrategyDirection.LONG,
    strength: StrategyStrength = StrategyStrength.STRONG,
    valid: bool = True,
) -> StrategyEvaluation:
    return StrategyEvaluation(
        strategy_name="EMABreakout",
        valid=valid,
        direction=direction,
        strength=strength,
        reasons=["all checks agree"],
        warnings=[],
    )


def make_risk_assessment(
    *,
    risk_ok: bool = True,
    position_size: int = 10,
    stop_loss: float = 95.0,
    target: float = 110.0,
    reward_risk_ratio: float = 2.0,
    capital_required: float = 1_000.0,
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


def make_order(order_manager: OrderManager, **overrides: object) -> Order:
    base: dict[str, object] = dict(
        strategy_name="EMABreakout",
        direction=StrategyDirection.LONG,
        requested_price=100.0,
        requested_quantity=10,
        stop_loss=95.0,
        target=110.0,
    )
    base.update(overrides)
    return order_manager.create_order(**base)  # type: ignore[arg-type]


def make_standalone_order(**overrides: object) -> Order:
    """An Order not registered with any OrderManager - for broker-level unit tests."""
    now = datetime(2026, 1, 5, 9, 30)
    base: dict[str, object] = dict(
        order_id="standalone-order",
        strategy_name="EMABreakout",
        direction=StrategyDirection.LONG,
        requested_price=100.0,
        requested_quantity=10,
        stop_loss=95.0,
        target=110.0,
        status=OrderStatus.SUBMITTED,
        created_at=now,
        updated_at=now,
    )
    base.update(overrides)
    return Order(**base)


def make_event_bus() -> EventBus:
    return EventBus()
