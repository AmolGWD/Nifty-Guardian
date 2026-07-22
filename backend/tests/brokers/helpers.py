from datetime import datetime
from typing import Any

from app.brokers.interface import KiteConnectClient
from app.paper_trading.models import Order, OrderStatus
from app.trading.strategy.models import StrategyDirection


def make_order(**overrides: object) -> Order:
    base: dict[str, object] = dict(
        order_id="local-order-1",
        strategy_name="EMABreakout",
        direction=StrategyDirection.LONG,
        requested_price=150.0,
        requested_quantity=50,
        stop_loss=145.0,
        target=160.0,
        status=OrderStatus.VALIDATED,
        created_at=datetime(2026, 1, 5, 9, 30),
        updated_at=datetime(2026, 1, 5, 9, 30),
    )
    base.update(overrides)
    return Order(**base)


class FakeKiteConnectClient(KiteConnectClient):
    """A fake satisfying KiteConnectClient - no real network calls, ever."""

    def __init__(
        self,
        *,
        placed_order_id: str = "KITE0001",
        order_history_response: list[dict[str, Any]] | None = None,
        positions_response: dict[str, Any] | None = None,
        holdings_response: list[dict[str, Any]] | None = None,
        profile_response: dict[str, Any] | None = None,
    ) -> None:
        self.placed_order_id = placed_order_id
        self.order_history_response = (
            order_history_response
            if order_history_response is not None
            else [{"status": "COMPLETE", "filled_quantity": 50, "average_price": 152.5}]
        )
        self.positions_response = (
            positions_response if positions_response is not None else {"net": [], "day": []}
        )
        self.holdings_response = holdings_response if holdings_response is not None else []
        self.profile_response = profile_response or {
            "user_id": "AB1234",
            "user_name": "Test User",
            "email": "test@example.com",
            "broker": "ZERODHA",
        }
        self.place_order_calls: list[dict[str, Any]] = []
        self.cancel_order_calls: list[dict[str, Any]] = []

    def place_order(self, **kwargs: Any) -> str:
        self.place_order_calls.append(kwargs)
        return self.placed_order_id

    def cancel_order(self, *, variety: str, order_id: str) -> str:
        self.cancel_order_calls.append({"variety": variety, "order_id": order_id})
        return order_id

    def order_history(self, order_id: str) -> list[dict[str, Any]]:
        return self.order_history_response

    def positions(self) -> dict[str, Any]:
        return self.positions_response

    def holdings(self) -> list[dict[str, Any]]:
        return self.holdings_response

    def profile(self) -> dict[str, Any]:
        return self.profile_response
