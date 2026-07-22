"""
Core types for Live Trading Mode: the session state machine, live
configuration (environment-driven, never hardcoded), and the small
value types safety/heartbeat/reconnect report through.

`LiveSessionState` is deliberately its own state machine, not a reuse
of `app.runtime.session_controller.SessionState` (frozen) - a live
session has connectivity-related states (Connecting/Connected/
Disconnected/Error) a replay-only runtime session never needed, and
conflating the two would either force replay-only states to grow
connectivity concerns they don't have, or force this package to
silently misuse states that don't mean what they'd need to mean here.
The transition table mirrors the same enforced-table discipline
`SESSION_STATE_TRANSITIONS`/`ORDER_STATUS_TRANSITIONS` (frozen)
already established.
"""

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class LiveSessionState(StrEnum):
    INITIALIZING = "Initializing"
    CONNECTING = "Connecting"
    CONNECTED = "Connected"
    TRADING = "Trading"
    PAUSED = "Paused"
    STOPPING = "Stopping"
    STOPPED = "Stopped"
    DISCONNECTED = "Disconnected"
    ERROR = "Error"


LIVE_SESSION_STATE_TRANSITIONS: dict[LiveSessionState, frozenset[LiveSessionState]] = {
    LiveSessionState.INITIALIZING: frozenset(
        {LiveSessionState.CONNECTING, LiveSessionState.STOPPING, LiveSessionState.ERROR}
    ),
    LiveSessionState.CONNECTING: frozenset(
        {
            LiveSessionState.CONNECTED,
            LiveSessionState.STOPPING,
            LiveSessionState.ERROR,
            LiveSessionState.DISCONNECTED,
        }
    ),
    LiveSessionState.CONNECTED: frozenset(
        {
            LiveSessionState.TRADING,
            LiveSessionState.DISCONNECTED,
            LiveSessionState.STOPPING,
            LiveSessionState.ERROR,
        }
    ),
    LiveSessionState.TRADING: frozenset(
        {
            LiveSessionState.PAUSED,
            LiveSessionState.DISCONNECTED,
            LiveSessionState.STOPPING,
            LiveSessionState.ERROR,
        }
    ),
    LiveSessionState.PAUSED: frozenset(
        {
            LiveSessionState.TRADING,
            LiveSessionState.DISCONNECTED,
            LiveSessionState.STOPPING,
            LiveSessionState.ERROR,
        }
    ),
    LiveSessionState.STOPPING: frozenset({LiveSessionState.STOPPED}),
    LiveSessionState.STOPPED: frozenset(),
    LiveSessionState.DISCONNECTED: frozenset(
        {LiveSessionState.CONNECTING, LiveSessionState.STOPPING, LiveSessionState.ERROR}
    ),
    LiveSessionState.ERROR: frozenset({LiveSessionState.STOPPING, LiveSessionState.CONNECTING}),
}


class InvalidLiveSessionTransitionError(ValueError):
    def __init__(self, current: LiveSessionState, target: LiveSessionState) -> None:
        super().__init__(f"cannot transition live session {current} -> {target}")


class LiveConfig(BaseSettings):
    """
    Every environment variable this phase names, loaded once, never
    hardcoded. `live_mode` defaults to `False` - the safe default is
    always "do not trade live" until explicitly turned on.
    """

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    live_mode: bool = False
    max_daily_loss: float = 10_000.0
    max_open_positions: int = 1
    max_orders_per_day: int = 10
    heartbeat_interval_seconds: float = 5.0
    reconnect_limit: int = 5
    trading_start: str = "09:15"
    trading_end: str = "15:30"

    @model_validator(mode="after")
    def _validate(self) -> "LiveConfig":
        if self.max_daily_loss <= 0:
            raise ValueError("MAX_DAILY_LOSS must be positive")
        if self.max_open_positions <= 0:
            raise ValueError("MAX_OPEN_POSITIONS must be positive")
        if self.max_orders_per_day <= 0:
            raise ValueError("MAX_ORDERS_PER_DAY must be positive")
        if self.heartbeat_interval_seconds <= 0:
            raise ValueError("HEARTBEAT_INTERVAL must be positive")
        if self.reconnect_limit <= 0:
            raise ValueError("RECONNECT_LIMIT must be positive")
        return self


class SafetyDecision(BaseModel):
    """One gate's verdict - every safety decision produces one of these, and every one is logged."""

    model_config = ConfigDict(frozen=True)

    gate: str
    allowed: bool
    reason: str


class HeartbeatSnapshot(BaseModel):
    model_config = ConfigDict(frozen=True)

    component: str
    last_seen_seconds_ago: float | None
    is_stale: bool


class ReconnectOutcome(BaseModel):
    model_config = ConfigDict(frozen=True)

    succeeded: bool
    attempts: int
    total_delay_seconds: float
