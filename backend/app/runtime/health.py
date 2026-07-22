"""
Tracks engine health purely from what the engine itself observes as it
runs (processed candles, per-candle processing latency, uptime) plus
what the event bus reports (events published, orders generated) -
mirrors `app.paper_trading.performance_monitor.PerformanceMonitor`'s
"learn everything from observation, compute nothing new" discipline.
`current_state` is read directly from a `SessionController`, not
duplicated.

Subscribes to every concrete event type individually (mirroring
`app.paper_trading.execution_journal.ExecutionJournal`'s actual
approach) rather than to `DomainEvent` itself - `EventBus.publish()`
dispatches by `type(event)` exactly, and no event is ever published as
a bare `DomainEvent` instance, so a wildcard subscription to the base
class would silently never fire despite what that module's own
docstring suggests. `app.paper_trading` is frozen this phase and
nothing there actually relies on that docstring's claim (a real defect
would need flagging and a minimal fix; a stale docstring describing a
never-exercised capability does not), so this module simply avoids
depending on it instead.
"""

import time

from pydantic import BaseModel, ConfigDict

from app.paper_trading.event_bus import EventBus
from app.paper_trading.events import (
    MarketDataReceivedEvent,
    OrderCancelledEvent,
    OrderFilledEvent,
    OrderPartiallyFilledEvent,
    OrderRejectedEvent,
    OrderSubmittedEvent,
    PortfolioUpdatedEvent,
    PositionUpdatedEvent,
    RiskApprovedEvent,
    SignalGeneratedEvent,
)
from app.runtime.session_controller import SessionController, SessionState

_ALL_EVENT_TYPES = (
    MarketDataReceivedEvent,
    SignalGeneratedEvent,
    RiskApprovedEvent,
    OrderSubmittedEvent,
    OrderPartiallyFilledEvent,
    OrderFilledEvent,
    OrderCancelledEvent,
    OrderRejectedEvent,
    PositionUpdatedEvent,
    PortfolioUpdatedEvent,
)


class HealthSnapshot(BaseModel):
    model_config = ConfigDict(frozen=True)

    processed_candles: int
    average_processing_latency_seconds: float | None
    uptime_seconds: float
    events_published: int
    orders_generated: int
    current_state: SessionState


class HealthMonitor:
    def __init__(self, event_bus: EventBus, session_controller: SessionController) -> None:
        self._session_controller = session_controller
        self._started_at = time.perf_counter()
        self._processed_candles = 0
        self._processing_latencies_seconds: list[float] = []
        self._events_published = 0
        self._orders_generated = 0

        for event_type in _ALL_EVENT_TYPES:
            event_bus.subscribe(event_type, self._on_any_event)
        event_bus.subscribe(OrderSubmittedEvent, self._on_order_submitted)

    def record_candle_processed(self, processing_latency_seconds: float) -> None:
        self._processed_candles += 1
        self._processing_latencies_seconds.append(processing_latency_seconds)

    def _on_any_event(self, event: object) -> None:
        self._events_published += 1

    def _on_order_submitted(self, event: OrderSubmittedEvent) -> None:
        self._orders_generated += 1

    def snapshot(self) -> HealthSnapshot:
        latencies = self._processing_latencies_seconds
        average_latency = sum(latencies) / len(latencies) if latencies else None

        return HealthSnapshot(
            processed_candles=self._processed_candles,
            average_processing_latency_seconds=average_latency,
            uptime_seconds=time.perf_counter() - self._started_at,
            events_published=self._events_published,
            orders_generated=self._orders_generated,
            current_state=self._session_controller.state,
        )
