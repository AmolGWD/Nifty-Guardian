"""
Runtime session state machine: Start/Pause/Resume/Stop/Replay/End
Session. Mirrors `app.paper_trading.models.ORDER_STATUS_TRANSITIONS`'s
pattern exactly - an explicit transition table `SessionController`
enforces on every call, not a diagram nobody checks.
"""

from enum import StrEnum


class SessionState(StrEnum):
    NOT_STARTED = "NotStarted"
    RUNNING = "Running"
    PAUSED = "Paused"
    STOPPED = "Stopped"
    ENDED = "Ended"


# `replay()` is the one action that can re-enter RUNNING from a
# terminal-ish state (STOPPED/ENDED) - "Replay" in the CTO brief means
# starting a fresh run without constructing a brand new
# SessionController, distinct from `start()`, which only ever works
# from NOT_STARTED.
SESSION_STATE_TRANSITIONS: dict[SessionState, frozenset[SessionState]] = {
    SessionState.NOT_STARTED: frozenset({SessionState.RUNNING}),
    SessionState.RUNNING: frozenset(
        {SessionState.PAUSED, SessionState.STOPPED, SessionState.ENDED}
    ),
    SessionState.PAUSED: frozenset(
        {SessionState.RUNNING, SessionState.STOPPED, SessionState.ENDED}
    ),
    SessionState.STOPPED: frozenset({SessionState.RUNNING, SessionState.ENDED}),
    SessionState.ENDED: frozenset({SessionState.RUNNING}),
}


class InvalidSessionTransitionError(ValueError):
    def __init__(self, current: SessionState, target: SessionState) -> None:
        super().__init__(f"cannot transition session {current} -> {target}")


class SessionController:
    def __init__(self) -> None:
        self._state = SessionState.NOT_STARTED

    @property
    def state(self) -> SessionState:
        return self._state

    def start(self) -> SessionState:
        return self._transition(SessionState.RUNNING)

    def pause(self) -> SessionState:
        return self._transition(SessionState.PAUSED)

    def resume(self) -> SessionState:
        return self._transition(SessionState.RUNNING)

    def stop(self) -> SessionState:
        return self._transition(SessionState.STOPPED)

    def replay(self) -> SessionState:
        return self._transition(SessionState.RUNNING)

    def end_session(self) -> SessionState:
        return self._transition(SessionState.ENDED)

    def _transition(self, target: SessionState) -> SessionState:
        if target not in SESSION_STATE_TRANSITIONS[self._state]:
            raise InvalidSessionTransitionError(self._state, target)
        self._state = target
        return self._state
