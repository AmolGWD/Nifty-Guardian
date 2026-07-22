"""
Owns the current `Order` for every order id and enforces
`ORDER_STATUS_TRANSITIONS` (models.py) on every state change - each
method replaces the stored `Order` with a new, validated instance
(never mutates one in place, per ADR-0006) and publishes the
corresponding event.
"""

import uuid
from datetime import datetime

from app.paper_trading.broker_interface import BrokerInterface
from app.paper_trading.event_bus import EventBus
from app.paper_trading.events import (
    OrderCancelledEvent,
    OrderFilledEvent,
    OrderPartiallyFilledEvent,
    OrderRejectedEvent,
    OrderSubmittedEvent,
)
from app.paper_trading.models import ORDER_STATUS_TRANSITIONS, Order, OrderStatus
from app.trading.strategy.models import StrategyDirection


class InvalidOrderTransitionError(ValueError):
    def __init__(self, order_id: str, current: OrderStatus, target: OrderStatus) -> None:
        super().__init__(f"order {order_id}: cannot transition {current} -> {target}")


class OrderManager:
    def __init__(self, event_bus: EventBus) -> None:
        self._event_bus = event_bus
        self._orders: dict[str, Order] = {}

    def create_order(
        self,
        *,
        strategy_name: str,
        direction: StrategyDirection,
        requested_price: float,
        requested_quantity: int,
        stop_loss: float,
        target: float,
    ) -> Order:
        now = datetime.now()
        order = Order(
            order_id=str(uuid.uuid4()),
            strategy_name=strategy_name,
            direction=direction,
            requested_price=requested_price,
            requested_quantity=requested_quantity,
            stop_loss=stop_loss,
            target=target,
            status=OrderStatus.NEW,
            created_at=now,
            updated_at=now,
        )
        self._orders[order.order_id] = order
        return order

    def validate(self, order_id: str) -> Order:
        return self._transition(order_id, OrderStatus.VALIDATED)

    def submit(self, order_id: str, broker: BrokerInterface) -> Order:
        order = self._transition(order_id, OrderStatus.SUBMITTED)
        self._event_bus.publish(
            OrderSubmittedEvent(event_id=str(uuid.uuid4()), timestamp=datetime.now(), order=order)
        )

        filled = broker.submit_order(order)
        self._require_valid_transition(order_id, order.status, filled.status)
        self._orders[order_id] = filled

        if filled.status == OrderStatus.FILLED:
            self._event_bus.publish(
                OrderFilledEvent(event_id=str(uuid.uuid4()), timestamp=datetime.now(), order=filled)
            )
        elif filled.status == OrderStatus.PARTIALLY_FILLED:
            self._event_bus.publish(
                OrderPartiallyFilledEvent(
                    event_id=str(uuid.uuid4()), timestamp=datetime.now(), order=filled
                )
            )
        return filled

    def cancel(self, order_id: str, broker: BrokerInterface) -> Order:
        order = self.get(order_id)
        cancelled = broker.cancel_order(order)
        self._require_valid_transition(order_id, order.status, cancelled.status)
        self._orders[order_id] = cancelled

        self._event_bus.publish(
            OrderCancelledEvent(
                event_id=str(uuid.uuid4()), timestamp=datetime.now(), order=cancelled
            )
        )
        return cancelled

    def reject(self, order_id: str, reason: str) -> Order:
        rejected = self._transition(order_id, OrderStatus.REJECTED, rejection_reason=reason)
        self._event_bus.publish(
            OrderRejectedEvent(event_id=str(uuid.uuid4()), timestamp=datetime.now(), order=rejected)
        )
        return rejected

    def get(self, order_id: str) -> Order:
        order = self._orders.get(order_id)
        if order is None:
            raise KeyError(f"no such order: {order_id}")
        return order

    def all_orders(self) -> tuple[Order, ...]:
        return tuple(self._orders.values())

    def _transition(self, order_id: str, target: OrderStatus, **extra_updates: object) -> Order:
        order = self.get(order_id)
        self._require_valid_transition(order_id, order.status, target)
        updated = order.model_copy(
            update={"status": target, "updated_at": datetime.now(), **extra_updates}
        )
        self._orders[order_id] = updated
        return updated

    def _require_valid_transition(
        self, order_id: str, current: OrderStatus, target: OrderStatus
    ) -> None:
        if target not in ORDER_STATUS_TRANSITIONS[current]:
            raise InvalidOrderTransitionError(order_id, current, target)
