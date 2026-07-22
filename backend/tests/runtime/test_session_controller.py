import pytest

from app.runtime.session_controller import (
    InvalidSessionTransitionError,
    SessionController,
    SessionState,
)


def test_initial_state_is_not_started() -> None:
    assert SessionController().state == SessionState.NOT_STARTED


def test_start_pause_resume_stop_end_happy_path() -> None:
    controller = SessionController()
    assert controller.start() == SessionState.RUNNING
    assert controller.pause() == SessionState.PAUSED
    assert controller.resume() == SessionState.RUNNING
    assert controller.stop() == SessionState.STOPPED
    assert controller.end_session() == SessionState.ENDED


def test_replay_reenters_running_from_stopped() -> None:
    controller = SessionController()
    controller.start()
    controller.stop()
    assert controller.replay() == SessionState.RUNNING


def test_replay_reenters_running_from_ended() -> None:
    controller = SessionController()
    controller.start()
    controller.stop()
    controller.end_session()
    assert controller.replay() == SessionState.RUNNING


def test_stop_directly_from_paused() -> None:
    controller = SessionController()
    controller.start()
    controller.pause()
    assert controller.stop() == SessionState.STOPPED


def test_end_session_directly_from_paused() -> None:
    controller = SessionController()
    controller.start()
    controller.pause()
    assert controller.end_session() == SessionState.ENDED


def test_cannot_pause_before_start() -> None:
    controller = SessionController()
    with pytest.raises(InvalidSessionTransitionError):
        controller.pause()


def test_cannot_start_twice() -> None:
    controller = SessionController()
    controller.start()
    with pytest.raises(InvalidSessionTransitionError):
        controller.start()


def test_cannot_resume_when_running() -> None:
    controller = SessionController()
    controller.start()
    with pytest.raises(InvalidSessionTransitionError):
        controller.resume()


def test_cannot_transition_out_of_ended_except_replay() -> None:
    controller = SessionController()
    controller.start()
    controller.stop()
    controller.end_session()
    with pytest.raises(InvalidSessionTransitionError):
        controller.pause()
    with pytest.raises(InvalidSessionTransitionError):
        controller.stop()


def test_error_message_names_both_states() -> None:
    controller = SessionController()
    with pytest.raises(InvalidSessionTransitionError, match="NotStarted -> Paused"):
        controller.pause()
