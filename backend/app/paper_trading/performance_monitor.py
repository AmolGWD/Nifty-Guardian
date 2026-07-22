"""
Tracks execution-quality and outcome metrics purely by observing the
event bus - orders submitted/filled/rejected/cancelled, fill ratio,
execution latency (time between `OrderSubmittedEvent` and
`OrderFilledEvent`), win rate (from closed positions' realized P&L),
daily return, and max drawdown (from `PortfolioUpdatedEvent`, reusing
`Portfolio.drawdown` rather than recomputing it). This module computes
no P&L itself - it only reads what `position_manager.py`/
`portfolio_manager.py` already computed.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.paper_trading.event_bus import EventBus
from app.paper_trading.events import (
    OrderCancelledEvent,
    OrderFilledEvent,
    OrderRejectedEvent,
    OrderSubmittedEvent,
    PortfolioUpdatedEvent,
    PositionUpdatedEvent,
)
from app.paper_trading.models import PositionStatus


class PerformanceSnapshot(BaseModel):
    model_config = ConfigDict(frozen=True)

    orders_submitted: int
    orders_filled: int
    orders_rejected: int
    orders_cancelled: int
    fill_ratio_percent: float
    daily_return_percent: float
    max_drawdown: float
    average_execution_latency_seconds: float | None
    win_rate_percent: float


class PerformanceMonitor:
    def __init__(self, event_bus: EventBus, *, initial_capital: float) -> None:
        self._initial_capital = initial_capital

        self._orders_submitted = 0
        self._orders_filled = 0
        self._orders_rejected = 0
        self._orders_cancelled = 0
        self._submitted_at: dict[str, datetime] = {}
        self._latencies_seconds: list[float] = []
        self._wins = 0
        self._losses = 0
        self._latest_daily_pnl = 0.0
        self._max_drawdown = 0.0

        event_bus.subscribe(OrderSubmittedEvent, self._on_submitted)
        event_bus.subscribe(OrderFilledEvent, self._on_filled)
        event_bus.subscribe(OrderRejectedEvent, self._on_rejected)
        event_bus.subscribe(OrderCancelledEvent, self._on_cancelled)
        event_bus.subscribe(PositionUpdatedEvent, self._on_position_updated)
        event_bus.subscribe(PortfolioUpdatedEvent, self._on_portfolio_updated)

    def _on_submitted(self, event: OrderSubmittedEvent) -> None:
        self._orders_submitted += 1
        self._submitted_at[event.order.order_id] = event.timestamp

    def _on_filled(self, event: OrderFilledEvent) -> None:
        self._orders_filled += 1
        submitted_at = self._submitted_at.get(event.order.order_id)
        if submitted_at is not None:
            self._latencies_seconds.append((event.timestamp - submitted_at).total_seconds())

    def _on_rejected(self, event: OrderRejectedEvent) -> None:
        self._orders_rejected += 1

    def _on_cancelled(self, event: OrderCancelledEvent) -> None:
        self._orders_cancelled += 1

    def _on_position_updated(self, event: PositionUpdatedEvent) -> None:
        if event.position.status != PositionStatus.CLOSED:
            return
        if event.position.realized_pnl > 0:
            self._wins += 1
        elif event.position.realized_pnl < 0:
            self._losses += 1

    def _on_portfolio_updated(self, event: PortfolioUpdatedEvent) -> None:
        self._latest_daily_pnl = event.portfolio.daily_pnl
        self._max_drawdown = max(self._max_drawdown, event.portfolio.drawdown)

    def snapshot(self) -> PerformanceSnapshot:
        fill_ratio = (
            self._orders_filled / self._orders_submitted * 100 if self._orders_submitted else 0.0
        )
        total_closed = self._wins + self._losses
        win_rate = (self._wins / total_closed * 100) if total_closed else 0.0
        daily_return = (
            self._latest_daily_pnl / self._initial_capital * 100 if self._initial_capital else 0.0
        )
        average_latency = (
            sum(self._latencies_seconds) / len(self._latencies_seconds)
            if self._latencies_seconds
            else None
        )

        return PerformanceSnapshot(
            orders_submitted=self._orders_submitted,
            orders_filled=self._orders_filled,
            orders_rejected=self._orders_rejected,
            orders_cancelled=self._orders_cancelled,
            fill_ratio_percent=round(fill_ratio, 4),
            daily_return_percent=round(daily_return, 4),
            max_drawdown=round(self._max_drawdown, 4),
            average_execution_latency_seconds=average_latency,
            win_rate_percent=round(win_rate, 4),
        )
