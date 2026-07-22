"""
Append-only record of every signal, order, execution, portfolio
change, and error - in-memory this phase (no database), the same
established pattern as `app.research.experiment_registry.
ExperimentRegistry`/`app.data.repository.HistoricalDataRepository`.
`subscribe_to()` wires this journal directly onto an `EventBus` so it
records every domain event as it happens, rather than needing every
manager to also call into the journal explicitly.
"""

import uuid
from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict

from app.paper_trading.event_bus import EventBus
from app.paper_trading.events import (
    DomainEvent,
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


class JournalEntryType(StrEnum):
    SIGNAL = "Signal"
    RISK = "Risk"
    ORDER = "Order"
    EXECUTION = "Execution"
    POSITION = "Position"
    PORTFOLIO = "Portfolio"
    ERROR = "Error"


class JournalEntry(BaseModel):
    model_config = ConfigDict(frozen=True)

    entry_id: str
    entry_type: JournalEntryType
    timestamp: datetime
    source_event_id: str
    description: str


_EVENT_TYPE_TO_ENTRY_TYPE: dict[type[DomainEvent], JournalEntryType] = {
    SignalGeneratedEvent: JournalEntryType.SIGNAL,
    RiskApprovedEvent: JournalEntryType.RISK,
    OrderSubmittedEvent: JournalEntryType.ORDER,
    OrderFilledEvent: JournalEntryType.EXECUTION,
    OrderPartiallyFilledEvent: JournalEntryType.EXECUTION,
    OrderCancelledEvent: JournalEntryType.ORDER,
    OrderRejectedEvent: JournalEntryType.ORDER,
    PositionUpdatedEvent: JournalEntryType.POSITION,
    PortfolioUpdatedEvent: JournalEntryType.PORTFOLIO,
}


class ExecutionJournal:
    def __init__(self) -> None:
        self._entries: list[JournalEntry] = []

    def subscribe_to(self, event_bus: EventBus) -> None:
        for event_type in _EVENT_TYPE_TO_ENTRY_TYPE:
            event_bus.subscribe(event_type, self._record_event)

    def record_error(self, description: str) -> JournalEntry:
        return self._record(
            JournalEntryType.ERROR, event_id=str(uuid.uuid4()), description=description
        )

    def all_entries(self) -> tuple[JournalEntry, ...]:
        return tuple(self._entries)

    def entries_by_type(self, entry_type: JournalEntryType) -> tuple[JournalEntry, ...]:
        return tuple(entry for entry in self._entries if entry.entry_type == entry_type)

    def _record_event(self, event: DomainEvent) -> None:
        entry_type = _EVENT_TYPE_TO_ENTRY_TYPE[type(event)]
        self._record(entry_type, event_id=event.event_id, description=repr(event))

    def _record(
        self, entry_type: JournalEntryType, *, event_id: str, description: str
    ) -> JournalEntry:
        entry = JournalEntry(
            entry_id=str(uuid.uuid4()),
            entry_type=entry_type,
            timestamp=datetime.now(),
            source_event_id=event_id,
            description=description,
        )
        self._entries.append(entry)
        return entry
