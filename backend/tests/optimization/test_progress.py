from app.optimization.progress import ProgressTracker


def test_initial_snapshot_before_any_recording() -> None:
    tracker = ProgressTracker(total_combinations=10)

    snapshot = tracker.snapshot()

    assert snapshot.total_combinations == 10
    assert snapshot.completed == 0
    assert snapshot.failed == 0
    assert snapshot.remaining == 10
    assert snapshot.estimated_remaining_seconds is None


def test_records_completed_and_failed_counts() -> None:
    tracker = ProgressTracker(total_combinations=4)

    tracker.record(failed=False)
    tracker.record(failed=True)
    tracker.record(failed=False)

    snapshot = tracker.snapshot()

    assert snapshot.completed == 3
    assert snapshot.failed == 1
    assert snapshot.remaining == 1


def test_estimates_remaining_time_once_progress_has_been_made() -> None:
    tracker = ProgressTracker(total_combinations=2)

    tracker.record(failed=False)
    snapshot = tracker.snapshot()

    assert snapshot.estimated_remaining_seconds is not None
    assert snapshot.estimated_remaining_seconds >= 0


def test_no_remaining_estimate_once_everything_is_completed() -> None:
    tracker = ProgressTracker(total_combinations=1)

    tracker.record(failed=False)
    snapshot = tracker.snapshot()

    assert snapshot.remaining == 0
    assert snapshot.estimated_remaining_seconds is None
