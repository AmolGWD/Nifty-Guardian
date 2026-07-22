"""
Paper Trading domain models - Order, Position, Portfolio - each a
frozen Pydantic model (ADR-0006), same discipline as every other
domain package. A "lifecycle" here means the same thing it means for
`Experiment`/`ExperimentResult` (Phase 14) or `RiskConfig`/
`CapitalState` (Phase 9): the value itself never mutates in place -
`order_manager.py`/`position_manager.py`/`portfolio_manager.py` hold
the current state and *replace* it with a new, validated instance on
every transition (`Order.model_copy(update=...)`, never
`order.status = ...`).

This module defines shapes only - no execution, no fills, no
connectivity. See `docs/PAPER_TRADING_GUIDE.md` for the full lifecycle
diagrams and `broker_interface.py`/`paper_broker.py` for the (still
simulation-only) broker abstraction.
"""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, model_validator

from app.config.validation import ParameterValidationError
from app.trading.strategy.models import StrategyDirection


class OrderStatus(StrEnum):
    NEW = "New"
    VALIDATED = "Validated"
    SUBMITTED = "Submitted"
    PARTIALLY_FILLED = "PartiallyFilled"
    FILLED = "Filled"
    CANCELLED = "Cancelled"
    REJECTED = "Rejected"


# Every legal transition, keyed by current status. Enforced by
# `order_manager.py`, not left to convention - see
# docs/PAPER_TRADING_GUIDE.md's "Order lifecycle" for the diagram this
# table renders.
ORDER_STATUS_TRANSITIONS: dict[OrderStatus, frozenset[OrderStatus]] = {
    OrderStatus.NEW: frozenset({OrderStatus.VALIDATED, OrderStatus.REJECTED}),
    OrderStatus.VALIDATED: frozenset({OrderStatus.SUBMITTED, OrderStatus.REJECTED}),
    OrderStatus.SUBMITTED: frozenset(
        {
            OrderStatus.FILLED,
            OrderStatus.PARTIALLY_FILLED,
            OrderStatus.CANCELLED,
            OrderStatus.REJECTED,
        }
    ),
    OrderStatus.PARTIALLY_FILLED: frozenset({OrderStatus.FILLED, OrderStatus.CANCELLED}),
    OrderStatus.FILLED: frozenset(),
    OrderStatus.CANCELLED: frozenset(),
    OrderStatus.REJECTED: frozenset(),
}

TERMINAL_ORDER_STATUSES: frozenset[OrderStatus] = frozenset(
    {OrderStatus.FILLED, OrderStatus.CANCELLED, OrderStatus.REJECTED}
)


class Order(BaseModel):
    model_config = ConfigDict(frozen=True)

    order_id: str
    strategy_name: str
    direction: StrategyDirection

    requested_price: float
    requested_quantity: int
    filled_quantity: int = 0
    average_fill_price: float | None = None

    stop_loss: float
    target: float

    status: OrderStatus = OrderStatus.NEW
    rejection_reason: str | None = None

    created_at: datetime
    updated_at: datetime

    @model_validator(mode="after")
    def _validate(self) -> "Order":
        if self.requested_quantity <= 0:
            raise ParameterValidationError("requested_quantity must be positive")
        if self.filled_quantity < 0:
            raise ParameterValidationError("filled_quantity cannot be negative")
        if self.filled_quantity > self.requested_quantity:
            raise ParameterValidationError("filled_quantity cannot exceed requested_quantity")
        return self

    @property
    def remaining_quantity(self) -> int:
        return self.requested_quantity - self.filled_quantity

    @property
    def is_terminal(self) -> bool:
        return self.status in TERMINAL_ORDER_STATUSES


class PositionStatus(StrEnum):
    OPEN = "Open"
    PARTIALLY_EXITED = "PartiallyExited"
    CLOSED = "Closed"


class Position(BaseModel):
    model_config = ConfigDict(frozen=True)

    position_id: str
    strategy_name: str
    direction: StrategyDirection

    average_entry_price: float
    quantity: int
    initial_quantity: int

    realized_pnl: float
    unrealized_pnl: float

    status: PositionStatus
    opened_at: datetime
    closed_at: datetime | None = None

    @model_validator(mode="after")
    def _validate(self) -> "Position":
        if self.initial_quantity <= 0:
            raise ParameterValidationError("initial_quantity must be positive")
        if self.quantity < 0:
            raise ParameterValidationError("quantity cannot be negative")
        if self.quantity > self.initial_quantity:
            raise ParameterValidationError("quantity cannot exceed initial_quantity")
        return self


class Portfolio(BaseModel):
    model_config = ConfigDict(frozen=True)

    as_of: datetime

    cash: float
    available_margin: float

    open_position_ids: tuple[str, ...]
    closed_position_ids: tuple[str, ...]

    daily_pnl: float
    total_equity: float
    peak_equity: float

    @property
    def drawdown(self) -> float:
        return max(0.0, self.peak_equity - self.total_equity)

    @property
    def drawdown_percent(self) -> float:
        if self.peak_equity <= 0:
            return 0.0
        return self.drawdown / self.peak_equity * 100
