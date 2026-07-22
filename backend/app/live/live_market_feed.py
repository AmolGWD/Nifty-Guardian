"""
Market feed abstraction only - per the CTO brief, no WebSocket
streaming this phase. `LiveMarketFeedInterface` is the seam a future
WebSocket-backed feed will implement; `ReplayMarketFeed` is this
phase's only concrete implementation, replaying an already-known
candle list and pushing each one to subscribers, simulating a live
feed's push semantics without any real network connectivity.

`LiveFeedMarketDataSource` bridges a push-based `LiveMarketFeedInterface`
into the frozen `app.runtime.market_data_source.MarketDataSource`
Protocol (pull-based: `__iter__`/`__len__`) - this is what lets
`live_runtime.py` reuse the frozen `RuntimeEngine` completely
unmodified, exactly as `docs/ENGINE_RUNTIME.md` already documents
`MarketDataSource` as a seam a "future live source would be a third
implementation of." Because `ReplayMarketFeed` (this phase's only
feed) has a known, finite candle count, `__len__` here is well-defined;
a true unbounded WebSocket feed (a later phase) will need to revisit
what `__len__` means for a feed with no fixed end - an honest, deferred
concern, not something this phase can resolve without inventing real
streaming infrastructure it was explicitly told not to build.
"""

import queue
import threading
import time
from collections.abc import Callable, Iterator
from typing import Protocol

from app.market_data.schemas import Candle


class LiveMarketFeedInterface(Protocol):
    def connect(self) -> None: ...

    def disconnect(self) -> None: ...

    def is_connected(self) -> bool: ...

    def subscribe(self, callback: Callable[[Candle], None]) -> None: ...


class ReplayMarketFeed:
    """
    Pushes an already-known candle list to subscribers, simulating a
    live feed's push semantics over replay data - no real connectivity
    of any kind. `run()` drives the push loop on the calling thread;
    callers that want it non-blocking should run it on their own
    thread (see `live_runtime.py`).
    """

    def __init__(self, candles: list[Candle], *, delay_seconds: float = 0.0) -> None:
        self._candles = candles
        self._delay_seconds = delay_seconds
        self._connected = False
        self._subscribers: list[Callable[[Candle], None]] = []
        self._stop_requested = False

    def connect(self) -> None:
        self._connected = True
        self._stop_requested = False

    def disconnect(self) -> None:
        self._connected = False
        self._stop_requested = True

    def is_connected(self) -> bool:
        return self._connected

    def subscribe(self, callback: Callable[[Candle], None]) -> None:
        self._subscribers.append(callback)

    def __len__(self) -> int:
        return len(self._candles)

    def run(self) -> None:
        """Pushes every candle to every subscriber, in order, until exhausted or disconnected."""
        for candle in self._candles:
            if not self._connected or self._stop_requested:
                return
            for callback in self._subscribers:
                callback(candle)
            if self._delay_seconds > 0:
                time.sleep(self._delay_seconds)


class LiveFeedMarketDataSource:
    """
    Adapts a push-based `LiveMarketFeedInterface` into the frozen,
    pull-based `MarketDataSource` Protocol `RuntimeEngine` expects -
    `RuntimeEngine` itself never changes. Subscribes to the feed at
    construction time and buffers pushed candles on a thread-safe
    queue; `__iter__` blocks (bounded by `queue_timeout_seconds`) for
    each next candle, stopping once `expected_length` candles have been
    yielded or the feed disconnects without producing one in time.
    """

    def __init__(
        self,
        feed: LiveMarketFeedInterface,
        *,
        expected_length: int,
        queue_timeout_seconds: float = 5.0,
    ) -> None:
        self._feed = feed
        self._expected_length = expected_length
        self._queue_timeout_seconds = queue_timeout_seconds
        self._queue: queue.Queue[Candle] = queue.Queue()
        feed.subscribe(self._queue.put)

    def __len__(self) -> int:
        return self._expected_length

    def __iter__(self) -> Iterator[Candle]:
        received = 0
        while received < self._expected_length:
            try:
                yield self._queue.get(timeout=self._queue_timeout_seconds)
                received += 1
            except queue.Empty:
                if not self._feed.is_connected():
                    return
                continue


def run_feed_in_background(feed: ReplayMarketFeed) -> threading.Thread:
    """Runs a `ReplayMarketFeed` on a background thread, so its `run()` loop doesn't block."""
    thread = threading.Thread(target=feed.run, daemon=True)
    thread.start()
    return thread
