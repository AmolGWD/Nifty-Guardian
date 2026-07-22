"""
Domain events published on `event_bus.py`. Every event is a frozen
Pydantic model - a fact that already happened, never a command or a
mutable in-progress record. Payloads reuse existing, already-approved
frozen domain types wherever one already exists (`app.market_data.
schemas.Candle`, `app.trading.strategy.models.StrategyEvaluation`,
`app.trading.risk.models.RiskAssessment`) rather than duplicating
their fields - this package only adds new types for concepts that
don't already have one (`Order`, `Position`, `Portfolio`, in
`models.py`).

`OrderRejectedEvent`/`OrderCancelledEvent`/`OrderPartiallyFilledEvent`
extend the CTO brief's named event list (`MarketDataReceived`,
`SignalGenerated`, `RiskApproved`, `OrderSubmitted`, `OrderFilled`,
`PositionUpdated`, `PortfolioUpdated`, `TradingSessionStarted`,
`TradingSessionEnded`) - the brief's own wording ("Support events such
as") frames that list as illustrative, and `OrderStatus`'s full
transition table (see `models.py`) has terminal states
(`REJECTED`/`CANCELLED`) and a partial-fill state that need their own
events to be observable on the bus, not folded into `OrderFilledEvent`.
"""

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict

from app.market_data.schemas import Candle
from app.paper_trading.market_session import SessionPhase
from app.paper_trading.models import Order, Portfolio, Position
from app.trading.risk.models import RiskAssessment
from app.trading.strategy.models import StrategyEvaluation


class DomainEvent(BaseModel):
    model_config = ConfigDict(frozen=True)

    event_id: str
    timestamp: datetime


class MarketDataReceivedEvent(DomainEvent):
    candle: Candle


class SignalGeneratedEvent(DomainEvent):
    evaluation: StrategyEvaluation


class RiskApprovedEvent(DomainEvent):
    risk_assessment: RiskAssessment


class OrderSubmittedEvent(DomainEvent):
    order: Order


class OrderPartiallyFilledEvent(DomainEvent):
    order: Order


class OrderFilledEvent(DomainEvent):
    order: Order


class OrderCancelledEvent(DomainEvent):
    order: Order


class OrderRejectedEvent(DomainEvent):
    order: Order


class PositionUpdatedEvent(DomainEvent):
    position: Position


class PortfolioUpdatedEvent(DomainEvent):
    portfolio: Portfolio


class TradingSessionStartedEvent(DomainEvent):
    session_date: date
    phase: SessionPhase


class TradingSessionEndedEvent(DomainEvent):
    session_date: date
    phase: SessionPhase
