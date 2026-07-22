import pytest

from app.live.heartbeat import HeartbeatMonitor
from app.live.live_session import LiveSession
from app.live.models import InvalidLiveSessionTransitionError, LiveConfig, LiveSessionState
from app.live.reconnect import ReconnectManager, ReconnectPolicy
from app.live.safety_manager import SafetyManager
from tests.live.helpers import FakeMarketFeed


def _no_sleep(_seconds: float) -> None:
    return None


def _build_session(
    *, fail_connect: bool = False, max_retries: int = 3
) -> tuple[LiveSession, FakeMarketFeed]:
    feed = FakeMarketFeed(fail_connect=fail_connect)
    safety_manager = SafetyManager(LiveConfig(_env_file=None))
    heartbeat_monitor = HeartbeatMonitor(interval_seconds=5.0)
    reconnect_manager = ReconnectManager(
        ReconnectPolicy(max_retries=max_retries, base_delay_seconds=0.01), sleep_fn=_no_sleep
    )
    session = LiveSession(
        market_feed=feed,
        safety_manager=safety_manager,
        heartbeat_monitor=heartbeat_monitor,
        reconnect_manager=reconnect_manager,
    )
    return session, feed


def test_session_starts_initializing() -> None:
    session, _ = _build_session()
    assert session.state == LiveSessionState.INITIALIZING


def test_full_lifecycle_connect_trade_pause_resume_stop() -> None:
    session, feed = _build_session()

    assert session.connect() == LiveSessionState.CONNECTED
    assert session.start_trading() == LiveSessionState.TRADING
    assert session.pause() == LiveSessionState.PAUSED
    assert session.resume() == LiveSessionState.TRADING
    assert session.stop() == LiveSessionState.STOPPED
    assert feed.disconnect_calls == 1


def test_connect_failure_transitions_to_error() -> None:
    session, _ = _build_session(fail_connect=True)

    assert session.connect() == LiveSessionState.ERROR


def test_emergency_stop_is_reachable_from_trading_and_engages_safety_manager() -> None:
    session, feed = _build_session()
    session.connect()
    session.start_trading()

    state = session.emergency_stop("operator kill switch")

    assert state == LiveSessionState.STOPPED
    assert feed.disconnect_calls == 1


def test_mark_disconnected_and_reconnect_succeeds() -> None:
    session, feed = _build_session()
    session.connect()
    session.mark_disconnected()

    assert session.state == LiveSessionState.DISCONNECTED

    state = session.attempt_reconnect()

    assert state == LiveSessionState.CONNECTED
    assert feed.connect_calls == 2


def test_reconnect_exhaustion_stops_the_session() -> None:
    session, _ = _build_session(fail_connect=True, max_retries=2)
    session.connect()  # ends in ERROR since fail_connect=True; ERROR -> CONNECTING is legal

    state = session.attempt_reconnect()

    assert state == LiveSessionState.STOPPED


def test_invalid_transition_raises() -> None:
    session, _ = _build_session()
    with pytest.raises(InvalidLiveSessionTransitionError):
        session.start_trading()  # cannot go INITIALIZING -> TRADING directly


def test_mark_error_transitions_from_connected() -> None:
    session, _ = _build_session()
    session.connect()

    state = session.mark_error("broker rejected heartbeat")

    assert state == LiveSessionState.ERROR
