from typing import Any

import pytest

from app.live.models import (
    LIVE_SESSION_STATE_TRANSITIONS,
    InvalidLiveSessionTransitionError,
    LiveConfig,
    LiveSessionState,
)


def _make_config(**overrides: Any) -> LiveConfig:
    return LiveConfig(_env_file=None, **overrides)


def test_every_state_has_a_transition_table_entry() -> None:
    assert set(LIVE_SESSION_STATE_TRANSITIONS.keys()) == set(LiveSessionState)


def test_stopped_and_stopping_are_terminal_or_near_terminal() -> None:
    assert LIVE_SESSION_STATE_TRANSITIONS[LiveSessionState.STOPPED] == frozenset()
    assert LIVE_SESSION_STATE_TRANSITIONS[LiveSessionState.STOPPING] == frozenset(
        {LiveSessionState.STOPPED}
    )


def test_invalid_transition_error_message_names_both_states() -> None:
    error = InvalidLiveSessionTransitionError(LiveSessionState.STOPPED, LiveSessionState.TRADING)
    assert "Stopped" in str(error)
    assert "Trading" in str(error)


def test_live_config_defaults_to_safe_values() -> None:
    config = _make_config()
    assert config.live_mode is False
    assert config.max_open_positions == 1


@pytest.mark.parametrize(
    "field",
    [
        "max_daily_loss",
        "max_open_positions",
        "max_orders_per_day",
        "heartbeat_interval_seconds",
        "reconnect_limit",
    ],
)
def test_live_config_rejects_non_positive_values(field: str) -> None:
    with pytest.raises(ValueError):
        _make_config(**{field: 0})
