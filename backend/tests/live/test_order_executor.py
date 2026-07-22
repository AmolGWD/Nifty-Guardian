import pytest

from app.brokers.errors import ConnectionError as BrokerConnectionError
from app.brokers.errors import OrderRejectedError
from app.live.order_executor import OrderExecutor
from app.paper_trading.models import OrderStatus
from tests.live.helpers import FakeBroker, make_order


def _no_sleep(_seconds: float) -> None:
    return None


def test_submit_order_returns_broker_result_and_tracks_status() -> None:
    broker = FakeBroker()
    executor = OrderExecutor(broker, sleep_fn=_no_sleep)
    order = make_order()

    result = executor.submit_order(order)

    assert result.status == OrderStatus.FILLED
    assert executor.last_known_status(order.order_id) == result
    assert broker.submit_calls == [order]


def test_cancel_order_returns_broker_result_and_tracks_status() -> None:
    broker = FakeBroker()
    executor = OrderExecutor(broker, sleep_fn=_no_sleep)
    order = make_order()

    result = executor.cancel_order(order)

    assert result.status == OrderStatus.CANCELLED
    assert executor.last_known_status(order.order_id) == result


def test_transient_failure_is_retried_and_eventually_succeeds() -> None:
    broker = FakeBroker(fail_times=2, failure_exception=BrokerConnectionError)
    executor = OrderExecutor(broker, max_retries=3, sleep_fn=_no_sleep)

    result = executor.submit_order(make_order())

    assert result.status == OrderStatus.FILLED
    assert len(broker.submit_calls) == 3


def test_transient_failure_raises_after_exhausting_max_retries() -> None:
    broker = FakeBroker(fail_times=5, failure_exception=BrokerConnectionError)
    executor = OrderExecutor(broker, max_retries=2, sleep_fn=_no_sleep)

    with pytest.raises(BrokerConnectionError):
        executor.submit_order(make_order())

    assert len(broker.submit_calls) == 3


def test_permanent_failure_is_never_retried() -> None:
    broker = FakeBroker(fail_times=5, failure_exception=OrderRejectedError)
    executor = OrderExecutor(broker, max_retries=3, sleep_fn=_no_sleep)

    with pytest.raises(OrderRejectedError):
        executor.submit_order(make_order())

    assert len(broker.submit_calls) == 1


def test_last_known_status_is_none_for_unknown_order() -> None:
    executor = OrderExecutor(FakeBroker(), sleep_fn=_no_sleep)
    assert executor.last_known_status("never-submitted") is None
