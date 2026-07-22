import pytest

from app.api.dashboard.dashboard_service import DashboardConflictError, DashboardRuntimeService
from app.runtime.engine_config import ReplaySpeed
from app.runtime.session_controller import SessionState
from tests.api.dashboard.helpers import wait_until


def test_initial_dashboard_snapshot_is_empty(fresh_service: DashboardRuntimeService) -> None:
    snapshot = fresh_service.dashboard_snapshot()

    assert snapshot.runtime.session_state == SessionState.NOT_STARTED
    assert snapshot.runtime.processed_candles == 0
    assert snapshot.current_candle is None
    assert snapshot.market_context is None
    assert snapshot.latest_signal is None
    assert snapshot.latest_recommendation is None
    assert snapshot.orders == []
    assert snapshot.positions == []
    assert snapshot.journal == []
    assert snapshot.portfolio.cash == 100_000.0


def test_initial_runtime_state_is_not_started(fresh_service: DashboardRuntimeService) -> None:
    assert fresh_service.runtime_state() == SessionState.NOT_STARTED


def test_start_transitions_to_running(fresh_service: DashboardRuntimeService) -> None:
    stats = fresh_service.start()
    assert stats.session_state == SessionState.RUNNING
    wait_until(lambda: fresh_service.runtime_state() != SessionState.NOT_STARTED)


def test_start_twice_raises_conflict(fresh_service: DashboardRuntimeService) -> None:
    fresh_service.start()
    with pytest.raises(DashboardConflictError):
        fresh_service.start()


def test_pause_before_start_raises_conflict(fresh_service: DashboardRuntimeService) -> None:
    with pytest.raises(DashboardConflictError):
        fresh_service.pause()


def test_resume_before_start_raises_conflict(fresh_service: DashboardRuntimeService) -> None:
    with pytest.raises(DashboardConflictError):
        fresh_service.resume()


def test_stop_before_start_raises_conflict(fresh_service: DashboardRuntimeService) -> None:
    with pytest.raises(DashboardConflictError):
        fresh_service.stop()


def test_pause_then_resume_round_trip(fresh_service: DashboardRuntimeService) -> None:
    fresh_service.start()
    stats = fresh_service.pause()
    assert stats.session_state == SessionState.PAUSED

    stats = fresh_service.resume()
    assert stats.session_state == SessionState.RUNNING


def test_stop_halts_the_session(fresh_service: DashboardRuntimeService) -> None:
    fresh_service.start()
    stats = fresh_service.stop()
    assert stats.session_state == SessionState.STOPPED


def test_replay_builds_a_fresh_session_with_requested_parameters(
    fresh_service: DashboardRuntimeService,
) -> None:
    stats = fresh_service.replay(replay_speed=ReplaySpeed.UNLIMITED, maximum_candles=10)

    # Unlimited + a tiny candle count can legitimately finish (and
    # auto-stop) before this assertion runs - both states are honest
    # reflections of the background thread's real progress.
    assert stats.session_state in (SessionState.RUNNING, SessionState.STOPPED)
    assert stats.replay_speed == ReplaySpeed.UNLIMITED
    assert stats.total_candles == 10


def test_replay_runs_to_completion_and_auto_stops(fresh_service: DashboardRuntimeService) -> None:
    fresh_service.replay(replay_speed=ReplaySpeed.UNLIMITED, maximum_candles=15)

    wait_until(lambda: fresh_service.runtime_state() == SessionState.STOPPED)

    snapshot = fresh_service.dashboard_snapshot()
    assert snapshot.runtime.processed_candles == 15
    assert snapshot.runtime.total_candles == 15


def test_replay_after_stop_discards_the_old_session(fresh_service: DashboardRuntimeService) -> None:
    fresh_service.replay(replay_speed=ReplaySpeed.UNLIMITED, maximum_candles=10)
    wait_until(lambda: fresh_service.runtime_state() == SessionState.STOPPED)

    stats = fresh_service.replay(replay_speed=ReplaySpeed.UNLIMITED, maximum_candles=20)

    # A brand-new session (fresh HealthMonitor) - total_candles reflects
    # the new request, not the discarded 10-candle session above.
    assert stats.total_candles == 20


def test_health_snapshot_before_start_is_empty(fresh_service: DashboardRuntimeService) -> None:
    health = fresh_service.health_snapshot()
    assert health.processed_candles == 0
    assert health.current_state == SessionState.NOT_STARTED


def test_market_context_appears_only_after_warmup(fresh_service: DashboardRuntimeService) -> None:
    fresh_service.replay(replay_speed=ReplaySpeed.UNLIMITED, maximum_candles=15)
    wait_until(lambda: fresh_service.runtime_state() == SessionState.STOPPED)

    # 15 candles < the 20-candle warmup EventProcessor requires - honestly null.
    snapshot = fresh_service.dashboard_snapshot()
    assert snapshot.market_context is None

    fresh_service.replay(replay_speed=ReplaySpeed.UNLIMITED, maximum_candles=40)
    wait_until(lambda: fresh_service.runtime_state() == SessionState.STOPPED)
    snapshot = fresh_service.dashboard_snapshot()
    assert snapshot.market_context is not None
    assert snapshot.current_candle is not None


def test_latest_recommendation_is_always_none_this_phase(
    fresh_service: DashboardRuntimeService,
) -> None:
    """
    Honest, documented gap (see dashboard_models.py's docstring): no
    event on the bus carries a TradeRecommendation, so this field is
    always None rather than a duplicated re-computation of the
    Strategy/Risk/Decision pipeline outside the package that owns it.
    """
    fresh_service.replay(replay_speed=ReplaySpeed.UNLIMITED, maximum_candles=40)
    wait_until(lambda: fresh_service.runtime_state() == SessionState.STOPPED)

    assert fresh_service.dashboard_snapshot().latest_recommendation is None
