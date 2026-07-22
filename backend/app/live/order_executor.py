"""
`OrderExecutor`: a `BrokerInterface`-compatible decorator around any
concrete broker (`PaperBroker` or `ZerodhaBroker`, both frozen) -
retries transient failures, tracks last-known order status, and is
given to `EventProcessor` as *its* broker. No trading logic: this
module never decides what to trade, only whether/how many times to
retry talking to whatever broker it wraps.

Because `OrderExecutor` satisfies `BrokerInterface` itself,
`app.paper_trading.order_manager.OrderManager` (frozen) - which
already calls `broker.submit_order()`/`broker.cancel_order()` and
publishes `OrderSubmittedEvent`/`OrderFilledEvent`/etc itself -
requires no changes at all to work with it. "Translate broker events
into runtime events" is therefore already handled by the frozen
`OrderManager`; this module's job is purely making the underlying
broker call reliable.

Retryable ("transient") failures: `ConnectionError`, `RateLimitError`,
`BrokerUnavailableError` (`app.brokers.errors`) - all represent "the
broker might work if we just try again." Not retried: `OrderRejectedError`
(the broker made a final decision), `AuthenticationError` (retrying
won't fix bad credentials), `MappingError` (this adapter's own
translation failed - retrying sends the same broken request again).
"""

import logging
import time
from collections.abc import Callable

from app.brokers.errors import BrokerUnavailableError, RateLimitError
from app.brokers.errors import ConnectionError as BrokerConnectionError
from app.paper_trading.broker_interface import BrokerInterface
from app.paper_trading.models import Order

logger = logging.getLogger(__name__)

_TRANSIENT_EXCEPTIONS = (BrokerConnectionError, RateLimitError, BrokerUnavailableError)


class OrderExecutor:
    def __init__(
        self,
        broker: BrokerInterface,
        *,
        max_retries: int = 3,
        retry_delay_seconds: float = 1.0,
        sleep_fn: Callable[[float], None] = time.sleep,
    ) -> None:
        self._broker = broker
        self._max_retries = max_retries
        self._retry_delay_seconds = retry_delay_seconds
        self._sleep_fn = sleep_fn
        self._last_known_status: dict[str, Order] = {}

    def submit_order(self, order: Order) -> Order:
        result = self._with_retry(lambda: self._broker.submit_order(order))
        self._last_known_status[result.order_id] = result
        return result

    def cancel_order(self, order: Order) -> Order:
        result = self._with_retry(lambda: self._broker.cancel_order(order))
        self._last_known_status[result.order_id] = result
        return result

    def last_known_status(self, order_id: str) -> Order | None:
        return self._last_known_status.get(order_id)

    def _with_retry(self, action: Callable[[], Order]) -> Order:
        attempt = 0
        while True:
            try:
                return action()
            except _TRANSIENT_EXCEPTIONS as exc:
                attempt += 1
                if attempt > self._max_retries:
                    logger.error(
                        "OrderExecutor: giving up after %d retries (%s): %s",
                        self._max_retries,
                        type(exc).__name__,
                        exc,
                    )
                    raise
                logger.warning(
                    "OrderExecutor: transient failure (%s), retrying (%d/%d): %s",
                    type(exc).__name__,
                    attempt,
                    self._max_retries,
                    exc,
                )
                self._sleep_fn(self._retry_delay_seconds)
