"""
Broker abstraction: the one seam between order management and however
orders actually get filled. `PaperBroker` (this phase) is the only
implementation - it simulates fills, with no live connectivity
whatsoever. A future live broker adapter (Zerodha or otherwise) would
implement this same `Protocol` without `order_manager.py` changing at
all - see docs/PAPER_TRADING_GUIDE.md's "Migration path to Live
Broker".
"""

from typing import Protocol

from app.paper_trading.models import Order


class BrokerInterface(Protocol):
    def submit_order(self, order: Order) -> Order: ...

    def cancel_order(self, order: Order) -> Order: ...
