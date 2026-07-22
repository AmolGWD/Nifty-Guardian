"""
Tracks portfolio-level state: cash, available margin, daily P&L, and
total equity - and, from the running peak of total equity ever
observed, drawdown. Reads open/closed positions from a
`PositionManager` rather than duplicating position bookkeeping - a
`Portfolio` snapshot is always a fresh view over "cash plus whatever
the positions are currently worth," never information this manager
maintains independently.
"""

import uuid
from datetime import datetime

from app.paper_trading.event_bus import EventBus
from app.paper_trading.events import PortfolioUpdatedEvent
from app.paper_trading.models import Portfolio
from app.paper_trading.position_manager import PositionManager


class PortfolioManager:
    def __init__(
        self,
        *,
        initial_cash: float,
        position_manager: PositionManager,
        event_bus: EventBus,
        initial_margin: float | None = None,
    ) -> None:
        self._cash = initial_cash
        self._available_margin = initial_margin if initial_margin is not None else initial_cash
        self._position_manager = position_manager
        self._event_bus = event_bus
        self._daily_pnl = 0.0
        self._peak_equity = initial_cash

    def record_cash_change(self, delta: float) -> None:
        """A realized P&L event (a trade closing) moves cash and today's running total."""
        self._cash = round(self._cash + delta, 4)
        self._daily_pnl = round(self._daily_pnl + delta, 4)

    def reset_daily_pnl(self) -> None:
        self._daily_pnl = 0.0

    def snapshot(self) -> Portfolio:
        open_positions = self._position_manager.open_positions()
        closed_positions = self._position_manager.closed_positions()

        total_equity = round(
            self._cash + sum(position.unrealized_pnl for position in open_positions), 4
        )
        self._peak_equity = max(self._peak_equity, total_equity)

        portfolio = Portfolio(
            as_of=datetime.now(),
            cash=self._cash,
            available_margin=self._available_margin,
            open_position_ids=tuple(p.position_id for p in open_positions),
            closed_position_ids=tuple(p.position_id for p in closed_positions),
            daily_pnl=self._daily_pnl,
            total_equity=total_equity,
            peak_equity=self._peak_equity,
        )
        self._event_bus.publish(
            PortfolioUpdatedEvent(
                event_id=str(uuid.uuid4()), timestamp=datetime.now(), portfolio=portfolio
            )
        )
        return portfolio
