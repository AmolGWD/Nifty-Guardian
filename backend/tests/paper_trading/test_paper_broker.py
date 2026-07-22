import pytest

from app.paper_trading.models import OrderStatus
from app.paper_trading.paper_broker import PaperBroker
from tests.paper_trading.helpers import make_standalone_order


def test_submit_order_fully_fills_at_requested_price() -> None:
    broker = PaperBroker()
    order = make_standalone_order(requested_price=105.0, requested_quantity=20)

    filled = broker.submit_order(order)

    assert filled.status == OrderStatus.FILLED
    assert filled.filled_quantity == 20
    assert filled.average_fill_price == 105.0


def test_submit_order_does_not_mutate_the_original_order() -> None:
    broker = PaperBroker()
    order = make_standalone_order()

    broker.submit_order(order)

    assert order.status == OrderStatus.SUBMITTED
    assert order.filled_quantity == 0


def test_cancel_order_transitions_to_cancelled() -> None:
    broker = PaperBroker()
    order = make_standalone_order()

    cancelled = broker.cancel_order(order)

    assert cancelled.status == OrderStatus.CANCELLED


def test_cancel_already_filled_order_raises() -> None:
    broker = PaperBroker()
    order = make_standalone_order(status=OrderStatus.FILLED, filled_quantity=10)

    with pytest.raises(ValueError, match="already"):
        broker.cancel_order(order)


def test_no_network_or_broker_client_imports() -> None:
    """A structural guard mirroring the CTO brief's 'no live connectivity' requirement."""
    import app.paper_trading.paper_broker as module

    source = module.__file__
    assert source is not None
    with open(source) as f:
        import_lines = [line for line in f if line.startswith(("import ", "from "))]
    for forbidden in ("kiteconnect", "websocket", "requests", "httpx"):
        assert not any(forbidden in line.lower() for line in import_lines)
