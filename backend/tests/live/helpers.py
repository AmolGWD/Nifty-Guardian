from datetime import datetime

from app.brokers.errors import BrokerError
from app.market_data.schemas import Candle
from app.paper_trading.models import Order, OrderStatus
from app.trading.strategy.models import StrategyDirection


def make_order(**overrides: object) -> Order:
    base: dict[str, object] = dict(
        order_id="live-order-1",
        strategy_name="EMABreakout",
        direction=StrategyDirection.LONG,
        requested_price=150.0,
        requested_quantity=50,
        stop_loss=145.0,
        target=160.0,
        status=OrderStatus.VALIDATED,
        created_at=datetime(2026, 1, 5, 9, 30),
        updated_at=datetime(2026, 1, 5, 9, 30),
    )
    base.update(overrides)
    return Order(**base)


def make_candles(n: int, *, start: datetime = datetime(2026, 1, 5, 9, 15)) -> list[Candle]:
    return [
        Candle(
            timestamp=start,
            open=100.0 + i,
            high=101.0 + i,
            low=99.0 + i,
            close=100.0 + i,
            volume=1000,
        )
        for i in range(n)
    ]


class FakeBroker:
    """A `BrokerInterface`-compatible fake - no real connectivity, ever."""

    def __init__(
        self,
        *,
        fail_times: int = 0,
        failure_exception: type[BrokerError] | None = None,
    ) -> None:
        self.submit_calls: list[Order] = []
        self.cancel_calls: list[Order] = []
        self._fail_times = fail_times
        self._failure_exception = failure_exception

    def submit_order(self, order: Order) -> Order:
        self.submit_calls.append(order)
        if self._fail_times > 0:
            self._fail_times -= 1
            assert self._failure_exception is not None
            raise self._failure_exception("simulated transient failure")
        return order.model_copy(
            update={
                "status": OrderStatus.FILLED,
                "filled_quantity": order.requested_quantity,
                "average_fill_price": order.requested_price,
            }
        )

    def cancel_order(self, order: Order) -> Order:
        self.cancel_calls.append(order)
        if self._fail_times > 0:
            self._fail_times -= 1
            assert self._failure_exception is not None
            raise self._failure_exception("simulated transient failure")
        return order.model_copy(update={"status": OrderStatus.CANCELLED})


class FakeMarketFeed:
    """A `LiveMarketFeedInterface`-compatible fake with controllable connect/disconnect."""

    def __init__(self, *, fail_connect: bool = False) -> None:
        self._connected = False
        self._fail_connect = fail_connect
        self.connect_calls = 0
        self.disconnect_calls = 0
        self._subscribers: list[object] = []

    def connect(self) -> None:
        self.connect_calls += 1
        if self._fail_connect:
            raise ConnectionError("simulated feed connect failure")
        self._connected = True

    def disconnect(self) -> None:
        self.disconnect_calls += 1
        self._connected = False

    def is_connected(self) -> bool:
        return self._connected

    def subscribe(self, callback: object) -> None:
        self._subscribers.append(callback)
