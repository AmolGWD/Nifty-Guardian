"""
A basic, in-memory metrics registry - counters and gauges only, no
histograms/percentiles, no external time-series backend. Good enough
to answer "is this process doing anything" from `/health/ready` or a
`/metrics` endpoint; a real deployment wanting Prometheus/Datadog-grade
metrics would replace this module, not extend it.
"""

import threading


class MetricsRegistry:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._counters: dict[str, float] = {}
        self._gauges: dict[str, float] = {}

    def increment(self, name: str, amount: float = 1.0) -> None:
        with self._lock:
            self._counters[name] = self._counters.get(name, 0.0) + amount

    def set_gauge(self, name: str, value: float) -> None:
        with self._lock:
            self._gauges[name] = value

    def snapshot(self) -> dict[str, dict[str, float]]:
        with self._lock:
            return {"counters": dict(self._counters), "gauges": dict(self._gauges)}

    def reset(self) -> None:
        """For tests only - production code never needs to clear the registry."""
        with self._lock:
            self._counters.clear()
            self._gauges.clear()


metrics_registry = MetricsRegistry()


def record_request(*, method: str, path: str, status_code: int, duration_seconds: float) -> None:
    """Convenience wrapper `app.main`'s request middleware calls once per request."""
    metrics_registry.increment("http_requests_total")
    metrics_registry.increment(f"http_requests_total{{method={method},status={status_code}}}")
    metrics_registry.set_gauge(f"http_request_duration_seconds{{path={path}}}", duration_seconds)
