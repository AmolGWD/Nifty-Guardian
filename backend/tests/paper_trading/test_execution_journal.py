import pytest
from pydantic import ValidationError

from app.paper_trading.event_bus import EventBus
from app.paper_trading.execution_journal import ExecutionJournal, JournalEntryType
from app.paper_trading.order_manager import OrderManager
from app.paper_trading.paper_broker import PaperBroker
from app.paper_trading.portfolio_manager import PortfolioManager
from app.paper_trading.position_manager import PositionManager
from app.trading.strategy.models import StrategyDirection
from tests.paper_trading.helpers import make_order


def test_records_order_submitted_and_filled() -> None:
    bus = EventBus()
    journal = ExecutionJournal()
    journal.subscribe_to(bus)

    manager = OrderManager(bus)
    order = make_order(manager)
    manager.validate(order.order_id)
    manager.submit(order.order_id, PaperBroker())

    order_entries = journal.entries_by_type(JournalEntryType.ORDER)
    execution_entries = journal.entries_by_type(JournalEntryType.EXECUTION)
    assert len(order_entries) == 1  # OrderSubmittedEvent
    assert len(execution_entries) == 1  # OrderFilledEvent


def test_records_rejection_as_order_entry() -> None:
    bus = EventBus()
    journal = ExecutionJournal()
    journal.subscribe_to(bus)

    manager = OrderManager(bus)
    order = make_order(manager)
    manager.reject(order.order_id, "test rejection")

    entries = journal.entries_by_type(JournalEntryType.ORDER)
    assert len(entries) == 1


def test_records_position_updates() -> None:
    bus = EventBus()
    journal = ExecutionJournal()
    journal.subscribe_to(bus)

    position_manager = PositionManager(bus)
    position_manager.open_position(
        strategy_name="EMABreakout", direction=StrategyDirection.LONG,
        entry_price=100.0, quantity=10,
    )

    entries = journal.entries_by_type(JournalEntryType.POSITION)
    assert len(entries) == 1


def test_records_portfolio_updates() -> None:
    bus = EventBus()
    journal = ExecutionJournal()
    journal.subscribe_to(bus)

    position_manager = PositionManager(bus)
    portfolio_manager = PortfolioManager(
        initial_cash=100_000.0, position_manager=position_manager, event_bus=bus
    )
    portfolio_manager.snapshot()

    entries = journal.entries_by_type(JournalEntryType.PORTFOLIO)
    assert len(entries) == 1


def test_record_error_adds_an_error_entry() -> None:
    journal = ExecutionJournal()

    entry = journal.record_error("something went wrong")

    assert entry.entry_type == JournalEntryType.ERROR
    assert "something went wrong" in entry.description
    assert len(journal.entries_by_type(JournalEntryType.ERROR)) == 1


def test_all_entries_returns_everything_in_order() -> None:
    bus = EventBus()
    journal = ExecutionJournal()
    journal.subscribe_to(bus)

    manager = OrderManager(bus)
    order = make_order(manager)
    manager.validate(order.order_id)
    manager.submit(order.order_id, PaperBroker())
    journal.record_error("a manual note")

    entries = journal.all_entries()
    assert len(entries) == 3
    assert entries[-1].entry_type == JournalEntryType.ERROR


def test_entries_are_immutable() -> None:
    journal = ExecutionJournal()
    entry = journal.record_error("test")

    with pytest.raises(ValidationError):
        entry.description = "changed"  # type: ignore[misc]
