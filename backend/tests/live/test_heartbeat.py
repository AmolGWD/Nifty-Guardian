from app.live.heartbeat import HeartbeatMonitor


class FakeClock:
    def __init__(self, start: float = 0.0) -> None:
        self._now = start

    def advance(self, seconds: float) -> None:
        self._now += seconds

    def __call__(self) -> float:
        return self._now


def test_unrecorded_component_is_stale_with_no_last_seen() -> None:
    monitor = HeartbeatMonitor(interval_seconds=5.0, clock=FakeClock())
    assert monitor.is_stale("broker") is True
    assert monitor.seconds_since_last_seen("broker") is None


def test_recorded_component_is_fresh_within_interval() -> None:
    clock = FakeClock()
    monitor = HeartbeatMonitor(interval_seconds=5.0, clock=clock)

    monitor.record("broker")
    clock.advance(2.0)

    assert monitor.is_stale("broker") is False
    assert monitor.seconds_since_last_seen("broker") == 2.0


def test_component_goes_stale_once_interval_elapses() -> None:
    clock = FakeClock()
    monitor = HeartbeatMonitor(interval_seconds=5.0, clock=clock)

    monitor.record("broker")
    clock.advance(6.0)

    assert monitor.is_stale("broker") is True


def test_snapshot_reports_component_state() -> None:
    clock = FakeClock()
    monitor = HeartbeatMonitor(interval_seconds=5.0, clock=clock)
    monitor.record("market_feed")

    snapshot = monitor.snapshot("market_feed")

    assert snapshot.component == "market_feed"
    assert snapshot.is_stale is False
    assert snapshot.last_seen_seconds_ago == 0.0


def test_all_snapshots_covers_every_tracked_component() -> None:
    monitor = HeartbeatMonitor(interval_seconds=5.0, clock=FakeClock())
    snapshots = monitor.all_snapshots()
    assert {s.component for s in snapshots} == {"broker", "market_feed", "runtime", "dashboard"}


def test_any_stale_is_false_when_nothing_has_been_recorded() -> None:
    monitor = HeartbeatMonitor(interval_seconds=5.0, clock=FakeClock())
    assert monitor.any_stale() is False


def test_any_stale_is_true_once_a_recorded_component_goes_stale() -> None:
    clock = FakeClock()
    monitor = HeartbeatMonitor(interval_seconds=5.0, clock=clock)
    monitor.record("broker")
    clock.advance(10.0)

    assert monitor.any_stale() is True
