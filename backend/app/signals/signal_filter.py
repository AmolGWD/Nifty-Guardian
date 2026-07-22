"""
Signal filtering: the gate between "a dummy trade was just opened"
and "the operator actually gets notified about it." Every check here
answers "should this particular signal reach the operator" - never
"should this trade be taken" (that's already decided, upstream, by the
frozen Strategy/Risk/Decision Engines by the time a signal reaches this
filter at all).

Trading-hours enforcement reads `app.core.config.settings.market_open`/
`market_close` - the same configuration values `app.runtime.
event_processor` itself compares against - but does so via a plain
`strftime("%H:%M")` string comparison, deliberately *not* by calling
`app.market_data.market_session.market_session_service` (which
converts its input to IST via `.astimezone()`). Every candle timestamp
flowing through this codebase is naive and already assumed to be local
market-clock time (exactly how `event_processor.py`'s own
`candle.timestamp.strftime("%H:%M") >= MARKET_CLOSE` treats it) - an
IST conversion on top of that assumption would silently shift the
comparison whenever this process's system timezone isn't IST itself,
which is exactly what a first version of this filter got wrong.
"""

import logging
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from enum import StrEnum

from app.core.config import settings
from app.signals.models import GuardianScore, SignalConfig

logger = logging.getLogger(__name__)


class SessionPhase(StrEnum):
    PRE_MARKET = "PreMarket"
    OPEN = "Open"
    CLOSED = "Closed"


def classify_session(timestamp: datetime) -> SessionPhase:
    """
    Same naive `strftime("%H:%M")` comparison `event_processor.py`
    itself uses for `MARKET_OPEN`/`MARKET_CLOSE` - no timezone
    conversion, since every candle timestamp in this codebase is
    already assumed to be local market-clock time.
    """
    current_time = timestamp.strftime("%H:%M")
    if current_time < settings.market_open:
        return SessionPhase.PRE_MARKET
    if current_time <= settings.market_close:
        return SessionPhase.OPEN
    return SessionPhase.CLOSED


def _is_within_trading_hours(timestamp: datetime) -> bool:
    return classify_session(timestamp) == SessionPhase.OPEN


@dataclass(frozen=True)
class FilterDecision:
    allowed: bool
    reason: str


@dataclass
class SignalFilter:
    config: SignalConfig
    _last_signal_at: dict[str, datetime] = field(default_factory=dict)
    _signals_today: int = field(default=0, init=False)
    _current_day: date | None = field(default=None, init=False)

    def _roll_day_if_needed(self, now: datetime) -> None:
        today = now.date()
        if self._current_day != today:
            self._current_day = today
            self._signals_today = 0

    def should_emit(
        self, *, strategy_name: str, guardian_score: GuardianScore, now: datetime
    ) -> FilterDecision:
        self._roll_day_if_needed(now)

        if not _is_within_trading_hours(now):
            return FilterDecision(
                allowed=False,
                reason=f"outside trading hours ({settings.market_open}-{settings.market_close})",
            )

        if guardian_score.score < self.config.confidence_threshold:
            return FilterDecision(
                allowed=False,
                reason=(
                    f"Guardian Score {guardian_score.score} below threshold "
                    f"{self.config.confidence_threshold}"
                ),
            )

        last_signal_at = self._last_signal_at.get(strategy_name)
        if last_signal_at is not None:
            cooldown = timedelta(minutes=self.config.cooldown_minutes)
            if now - last_signal_at < cooldown:
                return FilterDecision(allowed=False, reason="within cooldown of the last signal")

        if self._signals_today >= self.config.max_signals_per_day:
            return FilterDecision(
                allowed=False,
                reason=(
                    f"already sent {self._signals_today} signals today "
                    f"(max {self.config.max_signals_per_day})"
                ),
            )

        return FilterDecision(allowed=True, reason="all filters passed")

    def record_emitted(self, *, strategy_name: str, now: datetime) -> None:
        self._roll_day_if_needed(now)
        self._last_signal_at[strategy_name] = now
        self._signals_today += 1

    @property
    def signals_sent_today(self) -> int:
        return self._signals_today
