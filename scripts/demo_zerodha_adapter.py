#!/usr/bin/env python3
"""
Standalone demonstration of the Zerodha Broker Adapter (Phase 23).

Demonstrates authentication, fetching a profile, mapping an order,
mapping a position, and handling an error - entirely against a fake
`KiteConnectClient` returning hand-built, Kite-shaped responses. No
real credentials, no real API calls, no network access of any kind.

This is broker connectivity only - it does NOT place a real order,
does NOT connect to the real Kite Connect API, and does NOT change
any trading logic. Run from anywhere:

    python3 scripts/demo_zerodha_adapter.py
"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path
from typing import Any

_BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

from app.brokers.errors import MappingError, OrderRejectedError  # noqa: E402
from app.brokers.interface import KiteConnectClient  # noqa: E402
from app.brokers.zerodha_broker import ZerodhaBroker  # noqa: E402
from app.paper_trading.models import Order, OrderStatus  # noqa: E402
from app.trading.strategy.models import StrategyDirection  # noqa: E402


def _print_header(title: str) -> None:
    banner = "=" * 70
    print(f"\n{banner}\n{title}\n{banner}")


class DemoKiteClient(KiteConnectClient):
    """
    A fake `KiteConnectClient` returning hand-built, Kite-shaped
    responses - exactly what `tests/brokers/` also uses, so this demo
    exercises the identical code paths the test suite verifies. No
    real credentials, no real API calls.
    """

    def __init__(self, *, reject_orders: bool = False) -> None:
        self._reject_orders = reject_orders

    def place_order(self, **kwargs: Any) -> str:
        if self._reject_orders:
            # KiteConnectClient sits below ZerodhaKiteClient's exception
            # translation layer (kite_client.py) - a real KiteConnect
            # SDK failure would already have been translated into one
            # of our typed exceptions by the time it reaches here, so
            # this fake raises the translated exception directly
            # rather than a raw kiteconnect.exceptions.OrderException.
            raise OrderRejectedError("insufficient margin for this order")
        return "250722000012345"

    def cancel_order(self, *, variety: str, order_id: str) -> str:
        return order_id

    def order_history(self, order_id: str) -> list[dict[str, Any]]:
        return [
            {"status": "OPEN", "filled_quantity": 0, "average_price": None},
            {"status": "COMPLETE", "filled_quantity": 75, "average_price": 154.35},
        ]

    def positions(self) -> dict[str, Any]:
        return {
            "net": [
                {
                    "tradingsymbol": "NIFTY24JUL24000CE",
                    "exchange": "NFO",
                    "product": "MIS",
                    "quantity": 75,
                    "average_price": 154.35,
                    "last_price": 162.10,
                    "pnl": 581.25,
                }
            ]
        }

    def holdings(self) -> list[dict[str, Any]]:
        return []

    def profile(self) -> dict[str, Any]:
        return {
            "user_id": "AB1234",
            "user_name": "Demo Trader",
            "email": "demo.trader@example.com",
            "broker": "ZERODHA",
        }


def main() -> None:
    _print_header("1. AUTHENTICATION (mocked - no real credentials, no network)")
    client = DemoKiteClient()
    broker = ZerodhaBroker(
        client,
        trading_symbol_resolver=lambda order: "NIFTY24JUL24000CE",
    )
    print("Session validated against a fake KiteConnectClient (no real ZERODHA_* env vars used).")

    _print_header("2. FETCH PROFILE")
    profile = broker.get_profile()
    print(f"  user_id:   {profile.user_id}")
    print(f"  user_name: {profile.user_name}")
    print(f"  broker:    {profile.broker}")

    _print_header("3. MAP ORDER (internal Order -> Kite request -> Kite response -> Order)")
    order = Order(
        order_id="local-order-1",
        strategy_name="EMABreakout",
        direction=StrategyDirection.LONG,
        requested_price=154.35,
        requested_quantity=75,
        stop_loss=148.0,
        target=165.0,
        status=OrderStatus.VALIDATED,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    print(f"  Internal order before submission: status={order.status.value}, "
          f"quantity={order.requested_quantity}")

    filled_order = broker.submit_order(order)
    print(f"  Kite order_id:  {filled_order.order_id}")
    print(f"  Status:         {filled_order.status.value}")
    print(f"  Filled qty:     {filled_order.filled_quantity}")
    print(f"  Avg fill price: {filled_order.average_fill_price}")
    print(f"  strategy_name/stop_loss/target preserved from the original: "
          f"{filled_order.strategy_name}, {filled_order.stop_loss}, {filled_order.target}")

    _print_header("4. MAP POSITION")
    positions = broker.get_positions()
    for position in positions:
        print(f"  {position.trading_symbol} ({position.exchange}/{position.product}): "
              f"qty={position.quantity} avg={position.average_price} "
              f"last={position.last_price} pnl={position.pnl}")

    _print_header("5. HANDLE AN ERROR")
    rejecting_client = DemoKiteClient(reject_orders=True)
    rejecting_broker = ZerodhaBroker(
        rejecting_client, trading_symbol_resolver=lambda order: "NIFTY24JUL24000CE"
    )
    try:
        rejecting_broker.submit_order(order)
    except OrderRejectedError as exc:
        print(f"  Caught OrderRejectedError (a real kiteconnect.OrderException would "
              f"translate to this too - see kite_client.translate_kite_exception): {exc}")

    no_resolver_broker = ZerodhaBroker(client)
    try:
        no_resolver_broker.submit_order(order)
    except MappingError as exc:
        print(f"  Caught MappingError (no trading_symbol_resolver configured): {exc}")

    _print_header("Demo complete - no real order placed, no live connectivity used")


if __name__ == "__main__":
    main()
