"""
Scheduler: repeatedly calls a step function until it signals it's
done, with an optional delay between steps. `SynchronousScheduler` is
this phase's only implementation, per the CTO brief ("keep
implementation synchronous") - `Scheduler` is a `Protocol` specifically
so an async scheduler (awaiting a coroutine step, or driven by an
event loop instead of a plain `while` loop) can replace it later
without `runtime_engine.py` changing at all, the same seam
`app.paper_trading.broker_interface.BrokerInterface` already
established for brokers.

`sleep_fn` is injectable so tests never have to wait on a real clock -
pass a no-op (`lambda seconds: None`) to run at full speed regardless
of `EngineConfig.replay_speed`.
"""

import time
from collections.abc import Callable
from typing import Protocol


class Scheduler(Protocol):
    def run(self, step: Callable[[], bool], *, delay_seconds: float) -> None: ...


class SynchronousScheduler:
    def __init__(self, *, sleep_fn: Callable[[float], None] = time.sleep) -> None:
        self._sleep_fn = sleep_fn

    def run(self, step: Callable[[], bool], *, delay_seconds: float = 0.0) -> None:
        while True:
            should_continue = step()
            if not should_continue:
                return
            if delay_seconds > 0:
                self._sleep_fn(delay_seconds)
