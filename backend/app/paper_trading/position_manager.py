"""
Owns the current `Position` for every position id - opens one from a
filled order, updates unrealized P&L as new prices arrive, and closes
it (fully or partially) as exits happen. Every method replaces the
stored `Position` with a new instance (ADR-0006) and publishes
`PositionUpdatedEvent`.
"""

import uuid
from datetime import datetime

from app.paper_trading.event_bus import EventBus
from app.paper_trading.events import PositionUpdatedEvent
from app.paper_trading.models import Position, PositionStatus
from app.trading.strategy.models import StrategyDirection


def _signed_pnl(
    direction: StrategyDirection, entry_price: float, price: float, quantity: int
) -> float:
    sign = -1 if direction == StrategyDirection.SHORT else 1
    return round((price - entry_price) * quantity * sign, 4)


class PositionManager:
    def __init__(self, event_bus: EventBus) -> None:
        self._event_bus = event_bus
        self._positions: dict[str, Position] = {}

    def open_position(
        self,
        *,
        strategy_name: str,
        direction: StrategyDirection,
        entry_price: float,
        quantity: int,
    ) -> Position:
        now = datetime.now()
        position = Position(
            position_id=str(uuid.uuid4()),
            strategy_name=strategy_name,
            direction=direction,
            average_entry_price=entry_price,
            quantity=quantity,
            initial_quantity=quantity,
            realized_pnl=0.0,
            unrealized_pnl=0.0,
            status=PositionStatus.OPEN,
            opened_at=now,
        )
        self._positions[position.position_id] = position
        self._publish(position)
        return position

    def update_unrealized_pnl(self, position_id: str, current_price: float) -> Position:
        position = self.get(position_id)
        if position.status == PositionStatus.CLOSED:
            raise ValueError(f"cannot update a closed position: {position_id}")

        unrealized = _signed_pnl(
            position.direction, position.average_entry_price, current_price, position.quantity
        )
        updated = position.model_copy(update={"unrealized_pnl": unrealized})
        self._positions[position_id] = updated
        self._publish(updated)
        return updated

    def exit(self, position_id: str, *, exit_quantity: int, exit_price: float) -> Position:
        position = self.get(position_id)
        if position.status == PositionStatus.CLOSED:
            raise ValueError(f"cannot exit an already-closed position: {position_id}")
        if exit_quantity <= 0:
            raise ValueError("exit_quantity must be positive")
        if exit_quantity > position.quantity:
            raise ValueError(
                f"exit_quantity {exit_quantity} exceeds remaining quantity {position.quantity}"
            )

        realized_delta = _signed_pnl(
            position.direction, position.average_entry_price, exit_price, exit_quantity
        )
        remaining_quantity = position.quantity - exit_quantity
        now = datetime.now()

        if remaining_quantity == 0:
            updated = position.model_copy(
                update={
                    "quantity": 0,
                    "realized_pnl": round(position.realized_pnl + realized_delta, 4),
                    "unrealized_pnl": 0.0,
                    "status": PositionStatus.CLOSED,
                    "closed_at": now,
                }
            )
        else:
            updated = position.model_copy(
                update={
                    "quantity": remaining_quantity,
                    "realized_pnl": round(position.realized_pnl + realized_delta, 4),
                    "status": PositionStatus.PARTIALLY_EXITED,
                }
            )

        self._positions[position_id] = updated
        self._publish(updated)
        return updated

    def get(self, position_id: str) -> Position:
        position = self._positions.get(position_id)
        if position is None:
            raise KeyError(f"no such position: {position_id}")
        return position

    def open_positions(self) -> tuple[Position, ...]:
        return tuple(
            p for p in self._positions.values() if p.status != PositionStatus.CLOSED
        )

    def closed_positions(self) -> tuple[Position, ...]:
        return tuple(p for p in self._positions.values() if p.status == PositionStatus.CLOSED)

    def _publish(self, position: Position) -> None:
        self._event_bus.publish(
            PositionUpdatedEvent(
                event_id=str(uuid.uuid4()), timestamp=datetime.now(), position=position
            )
        )
