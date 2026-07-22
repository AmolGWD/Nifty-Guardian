"""
PaperBroker: the only `BrokerInterface` implementation this phase
defines. Simulates a fill by immediately filling the order in full, at
its own requested price - no live connectivity, no network call, no
Zerodha/websocket/REST anywhere in this module.

This is deliberately the simplest fill model that satisfies "PaperBroker
simulates fills" for this architecture-definition phase - realistic
candle-by-candle fill simulation (checking a live/replayed price
stream against stop-loss/target, as `app.trading.backtest.
trade_executor` already does for historical replay) is the Paper
Trading Engine's job, the next phase this one explicitly stops short
of. `order_manager.py` is the one place that calls into this broker
and publishes the resulting events - `PaperBroker` itself only ever
returns a new `Order`, it never touches the event bus.
"""

from datetime import datetime

from app.paper_trading.models import Order, OrderStatus


class PaperBroker:
    def submit_order(self, order: Order) -> Order:
        return order.model_copy(
            update={
                "status": OrderStatus.FILLED,
                "filled_quantity": order.requested_quantity,
                "average_fill_price": order.requested_price,
                "updated_at": datetime.now(),
            }
        )

    def cancel_order(self, order: Order) -> Order:
        if order.is_terminal:
            raise ValueError(f"cannot cancel order {order.order_id} - already {order.status}")

        return order.model_copy(
            update={"status": OrderStatus.CANCELLED, "updated_at": datetime.now()}
        )
