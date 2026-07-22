from app.observability.metrics import MetricsRegistry, metrics_registry, record_request


def test_increment_accumulates_across_calls() -> None:
    registry = MetricsRegistry()
    registry.increment("orders_submitted")
    registry.increment("orders_submitted")
    registry.increment("orders_submitted", amount=3.0)

    assert registry.snapshot()["counters"]["orders_submitted"] == 5.0


def test_increment_starts_from_zero_for_a_new_name() -> None:
    registry = MetricsRegistry()
    registry.increment("first_seen")

    assert registry.snapshot()["counters"]["first_seen"] == 1.0


def test_set_gauge_overwrites_rather_than_accumulates() -> None:
    registry = MetricsRegistry()
    registry.set_gauge("latency_seconds", 1.0)
    registry.set_gauge("latency_seconds", 2.5)

    assert registry.snapshot()["gauges"]["latency_seconds"] == 2.5


def test_snapshot_returns_independent_copies() -> None:
    registry = MetricsRegistry()
    registry.increment("counter_a")

    snapshot = registry.snapshot()
    snapshot["counters"]["counter_a"] = 999.0

    assert registry.snapshot()["counters"]["counter_a"] == 1.0


def test_reset_clears_both_counters_and_gauges() -> None:
    registry = MetricsRegistry()
    registry.increment("a")
    registry.set_gauge("b", 1.0)

    registry.reset()

    assert registry.snapshot() == {"counters": {}, "gauges": {}}


def test_record_request_updates_the_module_level_registry() -> None:
    metrics_registry.reset()

    record_request(method="GET", path="/health/live", status_code=200, duration_seconds=0.01)

    snapshot = metrics_registry.snapshot()
    assert snapshot["counters"]["http_requests_total"] == 1.0
    assert snapshot["counters"]["http_requests_total{method=GET,status=200}"] == 1.0
    assert "http_request_duration_seconds{path=/health/live}" in snapshot["gauges"]
