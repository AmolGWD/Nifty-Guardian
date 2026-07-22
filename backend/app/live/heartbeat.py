"""
Monitors broker connectivity, market feed, runtime health, and
dashboard connectivity - purely by observing timestamps components
report, mirroring `app.runtime.health.HealthMonitor`'s "learn
everything from observation, compute nothing new" discipline. A
component is "stale" once longer than `heartbeat_interval_seconds` has
passed since its last recorded heartbeat.
"""

import time
from collections.abc import Callable

from app.live.models import HeartbeatSnapshot

_TRACKED_COMPONENTS = ("broker", "market_feed", "runtime", "dashboard")


class HeartbeatMonitor:
    def __init__(
        self, *, interval_seconds: float, clock: Callable[[], float] = time.monotonic
    ) -> None:
        self._interval_seconds = interval_seconds
        self._clock = clock
        self._last_seen: dict[str, float] = {}

    def record(self, component: str) -> None:
        self._last_seen[component] = self._now()

    def is_stale(self, component: str) -> bool:
        last_seen = self._last_seen.get(component)
        if last_seen is None:
            return True
        return (self._now() - last_seen) > self._interval_seconds

    def seconds_since_last_seen(self, component: str) -> float | None:
        last_seen = self._last_seen.get(component)
        if last_seen is None:
            return None
        return self._now() - last_seen

    def snapshot(self, component: str) -> HeartbeatSnapshot:
        return HeartbeatSnapshot(
            component=component,
            last_seen_seconds_ago=self.seconds_since_last_seen(component),
            is_stale=self.is_stale(component),
        )

    def all_snapshots(self) -> list[HeartbeatSnapshot]:
        return [self.snapshot(component) for component in _TRACKED_COMPONENTS]

    def any_stale(self) -> bool:
        return any(
            self.is_stale(component)
            for component in _TRACKED_COMPONENTS
            if component in self._last_seen
        )

    def _now(self) -> float:
        return self._clock()
