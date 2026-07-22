import time
from collections.abc import Callable


def wait_until(
    predicate: Callable[[], bool], *, timeout: float = 3.0, interval: float = 0.02
) -> None:
    """Polls a background-thread-driven condition instead of a fixed sleep - avoids flaky timing."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return
        time.sleep(interval)
    raise AssertionError(f"condition not met within {timeout}s")
