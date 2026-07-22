"""
Reconnection with exponential backoff, a maximum retry count, and
graceful session restoration - explicitly, per the CTO brief, **no
automatic order replay**: reconnecting restores connectivity and lets
the session resume observing/trading again, but never resubmits
whatever order might have been in flight when the connection dropped.
Silently replaying an order after a disconnect risks placing a
duplicate the operator never asked for twice - the safer default is to
surface the gap and let a human (or `OrderExecutor`'s own status
tracking, in a later phase) decide, not guess.
"""

import logging
import time
from collections.abc import Callable

from app.live.models import ReconnectOutcome

logger = logging.getLogger(__name__)


class ReconnectPolicy:
    def __init__(
        self, *, max_retries: int, base_delay_seconds: float = 1.0, max_delay_seconds: float = 60.0
    ) -> None:
        self.max_retries = max_retries
        self.base_delay_seconds = base_delay_seconds
        self.max_delay_seconds = max_delay_seconds

    def next_delay(self, attempt: int) -> float:
        """Exponential backoff: base * 2^attempt, capped at max_delay_seconds."""
        return min(self.base_delay_seconds * (2.0**attempt), self.max_delay_seconds)


class ReconnectManager:
    def __init__(
        self, policy: ReconnectPolicy, *, sleep_fn: Callable[[float], None] = time.sleep
    ) -> None:
        self._policy = policy
        self._sleep_fn = sleep_fn

    def reconnect(self, attempt_connect: Callable[[], bool]) -> ReconnectOutcome:
        """
        Calls `attempt_connect()` (expected to return True on success)
        up to `policy.max_retries` times, sleeping an exponentially
        increasing delay between attempts. Never touches orders - see
        module docstring.
        """
        total_delay = 0.0
        for attempt in range(self._policy.max_retries):
            delay = self._policy.next_delay(attempt)
            logger.warning(
                "ReconnectManager: attempt %d/%d in %.1fs",
                attempt + 1,
                self._policy.max_retries,
                delay,
            )
            self._sleep_fn(delay)
            total_delay += delay

            if attempt_connect():
                logger.info("ReconnectManager: reconnected on attempt %d", attempt + 1)
                return ReconnectOutcome(
                    succeeded=True, attempts=attempt + 1, total_delay_seconds=total_delay
                )

        logger.error(
            "ReconnectManager: exhausted %d retries without reconnecting", self._policy.max_retries
        )
        return ReconnectOutcome(
            succeeded=False, attempts=self._policy.max_retries, total_delay_seconds=total_delay
        )
