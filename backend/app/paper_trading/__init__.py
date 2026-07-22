"""
Paper Trading Architecture (Phase 19).

Defines the complete event-driven architecture for paper trading -
models, events, an event bus, a broker abstraction (simulated fills
only), order/position/portfolio managers, an execution journal, a
market session abstraction, and a performance monitor. Does NOT
execute trades and does NOT connect to Zerodha or any live market
data - no websocket, no REST client, no network I/O anywhere in this
package. The continuous replay/live loop that would actually drive
these pieces together is the Paper Trading Engine, a later,
separately-reviewed phase. See docs/PAPER_TRADING_GUIDE.md.
"""

from app.paper_trading.broker_interface import BrokerInterface
from app.paper_trading.event_bus import EventBus
from app.paper_trading.events import (
    DomainEvent,
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
    TradingSessionEndedEvent,
    TradingSessionStartedEvent,
)
from app.paper_trading.execution_journal import ExecutionJournal, JournalEntry, JournalEntryType
from app.paper_trading.market_session import (
    ConfigurableCalendar,
    MarketCalendar,
    SessionPhase,
    SessionWindows,
)
from app.paper_trading.models import Order, OrderStatus, Portfolio, Position, PositionStatus
from app.paper_trading.order_manager import OrderManager
from app.paper_trading.paper_broker import PaperBroker
from app.paper_trading.performance_monitor import PerformanceMonitor, PerformanceSnapshot
from app.paper_trading.portfolio_manager import PortfolioManager
from app.paper_trading.position_manager import PositionManager

__all__ = [
    "BrokerInterface",
    "ConfigurableCalendar",
    "DomainEvent",
    "EventBus",
    "ExecutionJournal",
    "JournalEntry",
    "JournalEntryType",
    "MarketCalendar",
    "MarketDataReceivedEvent",
    "Order",
    "OrderCancelledEvent",
    "OrderFilledEvent",
    "OrderManager",
    "OrderPartiallyFilledEvent",
    "OrderRejectedEvent",
    "OrderStatus",
    "OrderSubmittedEvent",
    "PaperBroker",
    "PerformanceMonitor",
    "PerformanceSnapshot",
    "Portfolio",
    "PortfolioManager",
    "PortfolioUpdatedEvent",
    "Position",
    "PositionManager",
    "PositionStatus",
    "PositionUpdatedEvent",
    "RiskApprovedEvent",
    "SessionPhase",
    "SessionWindows",
    "SignalGeneratedEvent",
    "TradingSessionEndedEvent",
    "TradingSessionStartedEvent",
]
