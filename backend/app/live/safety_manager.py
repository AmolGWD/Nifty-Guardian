"""
Configurable safety gates for Live Trading Mode. Every gate answers
"is this action currently permitted" - the same "permission, not
decision" discipline `app.trading.conditions` (frozen) already
established at the market layer, just applied here to operational
limits (loss/position/order caps, trading hours, a kill switch, a
circuit breaker) instead of market conditions. `SafetyManager` never
decides *what* to trade - only whether the operator/system is
currently allowed to act at all.

Every decision - allowed or not - is logged, both via the standard
`logging` module and appended to an in-memory list any caller can
inspect (`decisions`), so a safety rejection is always auditable after
the fact, not just a silent `False`.
"""

import logging
from datetime import time as time_of_day

from app.live.models import LiveConfig, SafetyDecision

logger = logging.getLogger(__name__)


def _parse_time(value: str) -> time_of_day:
    hour, minute = value.split(":")
    return time_of_day(hour=int(hour), minute=int(minute))


class SafetyManager:
    def __init__(self, config: LiveConfig, *, circuit_breaker_threshold: int = 3) -> None:
        self._config = config
        self._trading_start = _parse_time(config.trading_start)
        self._trading_end = _parse_time(config.trading_end)
        self._circuit_breaker_threshold = circuit_breaker_threshold

        self._orders_today = 0
        self._realized_loss_today = 0.0
        self._open_positions = 0
        self._consecutive_failures = 0
        self._kill_switch_engaged = False
        self._emergency_stopped = False

        self.decisions: list[SafetyDecision] = []

    # -- state updates (called by the session as things happen) --

    def record_order_submitted(self) -> None:
        self._orders_today += 1

    def record_realized_pnl(self, amount: float) -> None:
        if amount < 0:
            self._realized_loss_today += -amount

    def record_position_opened(self) -> None:
        self._open_positions += 1

    def record_position_closed(self) -> None:
        self._open_positions = max(0, self._open_positions - 1)

    def record_order_outcome(self, *, succeeded: bool) -> None:
        self._consecutive_failures = 0 if succeeded else self._consecutive_failures + 1

    def reset_daily_counters(self) -> None:
        self._orders_today = 0
        self._realized_loss_today = 0.0

    # -- gates --

    def engage_kill_switch(self, reason: str) -> SafetyDecision:
        self._kill_switch_engaged = True
        return self._log(SafetyDecision(gate="kill_switch", allowed=False, reason=reason))

    def disengage_kill_switch(self) -> None:
        self._kill_switch_engaged = False

    def trigger_emergency_stop(self, reason: str) -> SafetyDecision:
        self._emergency_stopped = True
        return self._log(SafetyDecision(gate="emergency_stop", allowed=False, reason=reason))

    @property
    def is_emergency_stopped(self) -> bool:
        return self._emergency_stopped

    def is_within_trading_hours(self, now: time_of_day) -> bool:
        return self._trading_start <= now <= self._trading_end

    def check_before_order(self, now: time_of_day) -> SafetyDecision:
        """Runs every gate in order; returns the first rejection, or allowed if all pass."""
        if self._emergency_stopped:
            return self._log(
                SafetyDecision(
                    gate="emergency_stop", allowed=False, reason="emergency stop is active"
                )
            )
        if self._kill_switch_engaged:
            return self._log(
                SafetyDecision(gate="kill_switch", allowed=False, reason="kill switch is engaged")
            )
        if self._consecutive_failures >= self._circuit_breaker_threshold:
            return self._log(
                SafetyDecision(
                    gate="circuit_breaker",
                    allowed=False,
                    reason=f"{self._consecutive_failures} consecutive order failures",
                )
            )
        if not self.is_within_trading_hours(now):
            return self._log(
                SafetyDecision(
                    gate="trading_hours",
                    allowed=False,
                    reason=f"{now} is outside {self._trading_start}-{self._trading_end}",
                )
            )
        if self._orders_today >= self._config.max_orders_per_day:
            return self._log(
                SafetyDecision(
                    gate="max_orders_per_day",
                    allowed=False,
                    reason=f"{self._orders_today} orders already placed today "
                    f"(limit {self._config.max_orders_per_day})",
                )
            )
        if self._realized_loss_today >= self._config.max_daily_loss:
            return self._log(
                SafetyDecision(
                    gate="max_daily_loss",
                    allowed=False,
                    reason=f"realized loss {self._realized_loss_today} has reached the "
                    f"{self._config.max_daily_loss} limit",
                )
            )
        if self._open_positions >= self._config.max_open_positions:
            return self._log(
                SafetyDecision(
                    gate="max_open_positions",
                    allowed=False,
                    reason=f"{self._open_positions} open positions "
                    f"(limit {self._config.max_open_positions})",
                )
            )
        return self._log(
            SafetyDecision(gate="all_gates", allowed=True, reason="all safety gates passed")
        )

    def _log(self, decision: SafetyDecision) -> SafetyDecision:
        self.decisions.append(decision)
        level = logging.INFO if decision.allowed else logging.WARNING
        logger.log(
            level,
            "SafetyManager[%s]: allowed=%s - %s",
            decision.gate,
            decision.allowed,
            decision.reason,
        )
        return decision
