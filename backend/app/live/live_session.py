"""
`LiveSession`: the state machine tying together the market feed,
`OrderExecutor`, `SafetyManager`, `HeartbeatMonitor`, and
`ReconnectManager`. Every transition is checked against
`LIVE_SESSION_STATE_TRANSITIONS` (models.py), the same enforced-table
discipline `SessionController`/`OrderManager` (frozen) already
established. No trading logic lives here - this class only answers
"what operational state is the session in and is this transition
allowed," exactly mirroring `SessionController`'s own scope.
"""

import logging

from app.live.heartbeat import HeartbeatMonitor
from app.live.live_market_feed import LiveMarketFeedInterface
from app.live.models import (
    LIVE_SESSION_STATE_TRANSITIONS,
    InvalidLiveSessionTransitionError,
    LiveSessionState,
)
from app.live.reconnect import ReconnectManager
from app.live.safety_manager import SafetyManager

logger = logging.getLogger(__name__)


class LiveSession:
    def __init__(
        self,
        *,
        market_feed: LiveMarketFeedInterface,
        safety_manager: SafetyManager,
        heartbeat_monitor: HeartbeatMonitor,
        reconnect_manager: ReconnectManager,
    ) -> None:
        self._market_feed = market_feed
        self._safety_manager = safety_manager
        self._heartbeat_monitor = heartbeat_monitor
        self._reconnect_manager = reconnect_manager
        self._state = LiveSessionState.INITIALIZING

    @property
    def state(self) -> LiveSessionState:
        return self._state

    def connect(self) -> LiveSessionState:
        self._transition(LiveSessionState.CONNECTING)
        try:
            self._market_feed.connect()
        except Exception:
            logger.exception("LiveSession: connect() failed")
            return self._transition(LiveSessionState.ERROR)
        self._heartbeat_monitor.record("broker")
        self._heartbeat_monitor.record("market_feed")
        return self._transition(LiveSessionState.CONNECTED)

    def start_trading(self) -> LiveSessionState:
        return self._transition(LiveSessionState.TRADING)

    def pause(self) -> LiveSessionState:
        return self._transition(LiveSessionState.PAUSED)

    def resume(self) -> LiveSessionState:
        return self._transition(LiveSessionState.TRADING)

    def stop(self) -> LiveSessionState:
        self._transition(LiveSessionState.STOPPING)
        self._market_feed.disconnect()
        return self._transition(LiveSessionState.STOPPED)

    def emergency_stop(self, reason: str) -> LiveSessionState:
        """Callable from any non-terminal state - safety-critical, always allowed through."""
        self._safety_manager.trigger_emergency_stop(reason)
        logger.critical("LiveSession: EMERGENCY STOP - %s", reason)
        self._transition(LiveSessionState.STOPPING)
        self._market_feed.disconnect()
        return self._transition(LiveSessionState.STOPPED)

    def mark_disconnected(self) -> LiveSessionState:
        return self._transition(LiveSessionState.DISCONNECTED)

    def mark_error(self, reason: str) -> LiveSessionState:
        logger.error("LiveSession: entering ERROR state - %s", reason)
        return self._transition(LiveSessionState.ERROR)

    def attempt_reconnect(self) -> LiveSessionState:
        self._transition(LiveSessionState.CONNECTING)

        def _try_connect() -> bool:
            try:
                self._market_feed.connect()
                return self._market_feed.is_connected()
            except Exception:
                logger.exception("LiveSession: reconnect attempt failed")
                return False

        outcome = self._reconnect_manager.reconnect(_try_connect)
        if outcome.succeeded:
            self._heartbeat_monitor.record("broker")
            self._heartbeat_monitor.record("market_feed")
            return self._transition(LiveSessionState.CONNECTED)

        logger.error(
            "LiveSession: reconnect exhausted after %d attempts - stopping", outcome.attempts
        )
        self._transition(LiveSessionState.STOPPING)
        return self._transition(LiveSessionState.STOPPED)

    def _transition(self, target: LiveSessionState) -> LiveSessionState:
        if target not in LIVE_SESSION_STATE_TRANSITIONS[self._state]:
            raise InvalidLiveSessionTransitionError(self._state, target)
        logger.info("LiveSession: %s -> %s", self._state.value, target.value)
        self._state = target
        return self._state
