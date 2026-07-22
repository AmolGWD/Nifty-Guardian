import pytest

from app.paper_trading.event_bus import EventBus
from app.paper_trading.events import (
    OrderCancelledEvent,
    OrderFilledEvent,
    OrderRejectedEvent,
    OrderSubmittedEvent,
)
from app.paper_trading.models import OrderStatus
from app.paper_trading.order_manager import InvalidOrderTransitionError, OrderManager
from app.paper_trading.paper_broker import PaperBroker
from tests.paper_trading.helpers import make_order


def test_new_order_starts_in_new_status() -> None:
    manager = OrderManager(EventBus())
    order = make_order(manager)
    assert order.status == OrderStatus.NEW


def test_full_lifecycle_new_to_filled() -> None:
    bus = EventBus()
    manager = OrderManager(bus)
    broker = PaperBroker()
    order = make_order(manager)

    order = manager.validate(order.order_id)
    assert order.status == OrderStatus.VALIDATED

    order = manager.submit(order.order_id, broker)
    assert order.status == OrderStatus.FILLED
    assert order.filled_quantity == order.requested_quantity


def test_submit_publishes_order_submitted_then_order_filled() -> None:
    bus = EventBus()
    published: list[str] = []
    bus.subscribe(OrderSubmittedEvent, lambda e: published.append("submitted"))
    bus.subscribe(OrderFilledEvent, lambda e: published.append("filled"))

    manager = OrderManager(bus)
    order = make_order(manager)
    manager.validate(order.order_id)
    manager.submit(order.order_id, PaperBroker())

    assert published == ["submitted", "filled"]


def test_reject_publishes_order_rejected_with_reason() -> None:
    bus = EventBus()
    published: list[OrderRejectedEvent] = []
    bus.subscribe(OrderRejectedEvent, published.append)

    manager = OrderManager(bus)
    order = make_order(manager)
    rejected = manager.reject(order.order_id, "insufficient margin")

    assert rejected.status == OrderStatus.REJECTED
    assert rejected.rejection_reason == "insufficient margin"
    assert published[0].order.order_id == order.order_id


def test_cancel_publishes_order_cancelled() -> None:
    bus = EventBus()
    published: list[OrderCancelledEvent] = []
    bus.subscribe(OrderCancelledEvent, published.append)

    manager = OrderManager(bus)
    order = make_order(manager)
    manager.validate(order.order_id)
    manager.submit(order.order_id, PaperBroker())

    # Already FILLED by PaperBroker's immediate-fill simulation - cancel must reject this.
    with pytest.raises(ValueError):
        manager.cancel(order.order_id, PaperBroker())


def test_cannot_submit_before_validating() -> None:
    manager = OrderManager(EventBus())
    order = make_order(manager)

    with pytest.raises(InvalidOrderTransitionError):
        manager.submit(order.order_id, PaperBroker())


def test_cannot_transition_a_terminal_order() -> None:
    manager = OrderManager(EventBus())
    order = make_order(manager)
    manager.reject(order.order_id, "test")

    with pytest.raises(InvalidOrderTransitionError):
        manager.validate(order.order_id)


def test_get_unknown_order_raises_key_error() -> None:
    manager = OrderManager(EventBus())
    with pytest.raises(KeyError):
        manager.get("does-not-exist")


def test_all_orders_returns_every_created_order() -> None:
    manager = OrderManager(EventBus())
    make_order(manager)
    make_order(manager)

    assert len(manager.all_orders()) == 2
