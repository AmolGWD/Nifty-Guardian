"""
Lightweight, synchronous publish/subscribe event bus. `publish()` calls
every handler subscribed to the published event's exact type,
synchronously, in subscription order, before returning - there is no
queue, no thread, no async dispatch (per the CTO brief: "the
implementation may remain synchronous"). A handler that raises
propagates immediately to the caller of `publish()`, the same as a
plain function call would - this bus adds no error isolation between
handlers, since the whole point at this phase is a simple, traceable,
single-threaded event flow (see the demo script).

Subscribing to a subclass does not receive events of its parent type
or vice versa - `publish()` dispatches by `type(event)` exactly, not
`isinstance`. Subscribe to `DomainEvent` itself to observe every event
regardless of its concrete type (see `execution_journal.py`).
"""

from collections import defaultdict
from collections.abc import Callable
from typing import TypeVar

from app.paper_trading.events import DomainEvent

E = TypeVar("E", bound=DomainEvent)


class EventBus:
    def __init__(self) -> None:
        self._handlers: dict[type[DomainEvent], list[Callable[..., None]]] = defaultdict(list)

    def subscribe(self, event_type: type[E], handler: Callable[[E], None]) -> None:
        self._handlers[event_type].append(handler)

    def publish(self, event: DomainEvent) -> None:
        for handler in self._handlers.get(type(event), []):
            handler(event)

    def handler_count(self, event_type: type[DomainEvent]) -> int:
        return len(self._handlers.get(event_type, []))
