"""
`ZerodhaBroker`: implements `app.paper_trading.broker_interface.
BrokerInterface` (frozen) - `submit_order`/`cancel_order`, both typed
against `app.paper_trading.models.Order`, exactly as `PaperBroker`
(frozen, untouched) already does. `order_manager.py` (frozen) can hold
either broker without knowing which one it has.

One deliberate, honestly-flagged limitation: `Order` (frozen,
app.paper_trading) carries no instrument identifier - PaperBroker
never needed one, since it simulates a fill in the abstract without
knowing which real contract it's for. A live Zerodha order absolutely
needs a trading symbol + exchange to know *what* to buy. Resolving
"which real NIFTY options contract does this Order correspond to" is
explicitly Live Trading Mode's job (the next, not-yet-authorized
phase) - not this adapter's. `trading_symbol_resolver` is the seam
that phase will fill in; until then, the default resolver raises
`MappingError` loudly rather than silently guessing a wrong symbol.
"""

from collections.abc import Callable

from app.brokers.authentication import ZerodhaCredentials, validate_session
from app.brokers.errors import MappingError
from app.brokers.interface import KiteConnectClient
from app.brokers.kite_client import ZerodhaKiteClient, build_kite_connect_client
from app.brokers.mapper import (
    build_kite_order_request,
    map_kite_holding,
    map_kite_order_update,
    map_kite_position,
)
from app.brokers.models import BrokerHolding, BrokerPosition, BrokerProfile
from app.paper_trading.models import Order


def _default_trading_symbol_resolver(order: Order) -> str:
    raise MappingError(
        f"no trading_symbol_resolver configured - Order {order.order_id} carries no "
        "instrument identifier (app.paper_trading.models.Order has none; PaperBroker never "
        "needed one). Live Trading Mode must supply a resolver before placing real orders."
    )


class ZerodhaBroker:
    def __init__(
        self,
        client: KiteConnectClient,
        *,
        default_exchange: str = "NFO",
        default_product: str = "MIS",
        default_order_type: str = "MARKET",
        default_variety: str = "regular",
        trading_symbol_resolver: Callable[[Order], str] = _default_trading_symbol_resolver,
    ) -> None:
        self._client = client
        self._exchange = default_exchange
        self._product = default_product
        self._order_type = default_order_type
        self._variety = default_variety
        self._resolve_trading_symbol = trading_symbol_resolver

    # -- BrokerInterface --

    def submit_order(self, order: Order) -> Order:
        trading_symbol = self._resolve_trading_symbol(order)
        request = build_kite_order_request(
            order,
            trading_symbol=trading_symbol,
            exchange=self._exchange,
            product=self._product,
            order_type=self._order_type,
            variety=self._variety,
        )
        kite_order_id = self._client.place_order(**request)
        return self._refresh_order(order, kite_order_id)

    def cancel_order(self, order: Order) -> Order:
        kite_order_id = self._client.cancel_order(variety=self._variety, order_id=order.order_id)
        return self._refresh_order(order, kite_order_id)

    def _refresh_order(self, order: Order, kite_order_id: str) -> Order:
        history = self._client.order_history(kite_order_id)
        if not history:
            raise MappingError(f"Kite returned no order history for order_id={kite_order_id!r}")
        latest = history[-1]
        return map_kite_order_update(order.model_copy(update={"order_id": kite_order_id}), latest)

    # -- Additional broker read capabilities (beyond BrokerInterface's minimal surface) --

    def get_positions(self) -> list[BrokerPosition]:
        raw = self._client.positions()
        return [map_kite_position(position) for position in raw.get("net", [])]

    def get_holdings(self) -> list[BrokerHolding]:
        return [map_kite_holding(holding) for holding in self._client.holdings()]

    def get_profile(self) -> BrokerProfile:
        return validate_session(self._client)


def build_zerodha_broker(
    credentials: ZerodhaCredentials,
    *,
    default_exchange: str = "NFO",
    default_product: str = "MIS",
    default_order_type: str = "MARKET",
    default_variety: str = "regular",
    trading_symbol_resolver: Callable[[Order], str] = _default_trading_symbol_resolver,
) -> ZerodhaBroker:
    """
    The one end-to-end factory: credentials -> authenticated SDK
    client -> validated session (eagerly surfacing an expired/invalid
    `ZERODHA_ACCESS_TOKEN` as `AuthenticationError` before any order is
    ever attempted) -> a ready-to-use `ZerodhaBroker`.
    """
    kite = build_kite_connect_client(
        api_key=credentials.api_key, access_token=credentials.access_token
    )
    client = ZerodhaKiteClient(kite)
    validate_session(client)
    return ZerodhaBroker(
        client,
        default_exchange=default_exchange,
        default_product=default_product,
        default_order_type=default_order_type,
        default_variety=default_variety,
        trading_symbol_resolver=trading_symbol_resolver,
    )
