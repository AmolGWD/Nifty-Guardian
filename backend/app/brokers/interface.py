"""
`KiteConnectClient`: the one seam between this adapter and the
`kiteconnect` SDK, mirroring `app.market_data.client.MarketDataClient`'s
established pattern exactly - every SDK call this package makes goes
through this `Protocol`, so `zerodha_broker.py`/`authentication.py` are
testable with a fake and never import `kiteconnect` themselves.
Raw dicts in, raw dicts out - the same shape the real `KiteConnect`
SDK itself returns; `mapper.py` is the only place those dicts become
this adapter's own types.

`BrokerInterface` (the *outward*-facing Protocol `ZerodhaBroker` must
satisfy) already exists, frozen, at
`app.paper_trading.broker_interface.BrokerInterface` - it is imported,
not redefined, in `zerodha_broker.py`.
"""

from typing import Any, Protocol


class KiteConnectClient(Protocol):
    def place_order(
        self,
        *,
        variety: str,
        exchange: str,
        tradingsymbol: str,
        transaction_type: str,
        quantity: int,
        product: str,
        order_type: str,
        price: float | None = None,
    ) -> str: ...

    def cancel_order(self, *, variety: str, order_id: str) -> str: ...

    def order_history(self, order_id: str) -> list[dict[str, Any]]: ...

    def positions(self) -> dict[str, Any]: ...

    def holdings(self) -> list[dict[str, Any]]: ...

    def profile(self) -> dict[str, Any]: ...
