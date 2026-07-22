"""
Concrete `KiteConnectClient` (interface.py) wrapping a real
`KiteConnect` instance. No business logic here - every method is a
direct SDK call, translating `kiteconnect.exceptions.KiteException`
(and subclasses) into this package's own typed exceptions
(errors.py). This is the only module in `app.brokers` that imports
`kiteconnect` - `authentication.py`/`mapper.py`/`zerodha_broker.py`
all depend on `interface.KiteConnectClient` instead, the same
`Protocol`-seam discipline `app.market_data.client.MarketDataClient`
already established.
"""

from typing import Any

from kiteconnect import KiteConnect
from kiteconnect.exceptions import (
    DataException,
    GeneralException,
    InputException,
    KiteException,
    NetworkException,
    OrderException,
    PermissionException,
    TokenException,
)

from app.brokers.errors import (
    AuthenticationError,
    BrokerError,
    BrokerUnavailableError,
    MappingError,
    OrderRejectedError,
    RateLimitError,
)
from app.brokers.errors import (
    ConnectionError as BrokerConnectionError,
)


def translate_kite_exception(exc: KiteException) -> BrokerError:
    """The one place a `kiteconnect` exception becomes one of ours - never re-raised as-is."""
    if getattr(exc, "code", None) == 429:
        return RateLimitError(str(exc))
    if isinstance(exc, TokenException | PermissionException):
        return AuthenticationError(str(exc))
    if isinstance(exc, NetworkException):
        return BrokerConnectionError(str(exc))
    if isinstance(exc, OrderException):
        return OrderRejectedError(str(exc))
    if isinstance(exc, InputException):
        return MappingError(str(exc))
    if isinstance(exc, GeneralException | DataException):
        return BrokerUnavailableError(str(exc))
    return BrokerUnavailableError(str(exc))


class ZerodhaKiteClient:
    def __init__(self, kite: KiteConnect) -> None:
        self._kite = kite

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
    ) -> str:
        try:
            return str(
                self._kite.place_order(
                    variety=variety,
                    exchange=exchange,
                    tradingsymbol=tradingsymbol,
                    transaction_type=transaction_type,
                    quantity=quantity,
                    product=product,
                    order_type=order_type,
                    price=price,
                )
            )
        except KiteException as exc:
            raise translate_kite_exception(exc) from exc

    def cancel_order(self, *, variety: str, order_id: str) -> str:
        try:
            return str(self._kite.cancel_order(variety=variety, order_id=order_id))
        except KiteException as exc:
            raise translate_kite_exception(exc) from exc

    def order_history(self, order_id: str) -> list[dict[str, Any]]:
        try:
            return list(self._kite.order_history(order_id))
        except KiteException as exc:
            raise translate_kite_exception(exc) from exc

    def positions(self) -> dict[str, Any]:
        try:
            return dict(self._kite.positions())
        except KiteException as exc:
            raise translate_kite_exception(exc) from exc

    def holdings(self) -> list[dict[str, Any]]:
        try:
            return list(self._kite.holdings())
        except KiteException as exc:
            raise translate_kite_exception(exc) from exc

    def profile(self) -> dict[str, Any]:
        try:
            return dict(self._kite.profile())
        except KiteException as exc:
            raise translate_kite_exception(exc) from exc


def build_kite_connect_client(*, api_key: str, access_token: str) -> KiteConnect:
    """Factory for a real, authenticated `KiteConnect` instance (mirrors app.kite.client)."""
    kite = KiteConnect(api_key=api_key)
    kite.set_access_token(access_token)
    return kite
