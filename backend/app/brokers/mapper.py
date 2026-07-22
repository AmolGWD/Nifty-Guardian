"""
Every translation between a Kite Connect payload (a plain dict, as the
SDK returns it) and this codebase's own types. No Kite SDK object or
raw Kite dict ever crosses out of `zerodha_broker.py` - every field
this adapter exposes comes from one of the functions below.

`app.paper_trading.models.Order` (frozen) is reused directly for order
mapping, since `BrokerInterface.submit_order()`/`cancel_order()`
already mandates that exact type - there is no separate "internal
Order" type to invent. A full Kite order response cannot become an
`Order` on its own, though: `strategy_name`/`stop_loss`/`target` are
this codebase's own fields, not Zerodha's - `map_kite_order_update()`
therefore takes the *original* internal `Order` and merges Kite's
status/fill data onto it via `model_copy()`, the same pattern
`OrderManager._transition()` (frozen) already uses.

Kite's order status vocabulary is richer than this codebase's
`OrderStatus` (NEW/VALIDATED/SUBMITTED/PARTIALLY_FILLED/FILLED/
CANCELLED/REJECTED) - every Kite pending/intermediate status
(`OPEN`, `TRIGGER PENDING`, `OPEN PENDING`, `VALIDATION PENDING`,
`MODIFY PENDING`, `PUT ORDER REQ RECEIVED`, `AMO REQ RECEIVED`)
collapses to `SUBMITTED`, an explicit, documented simplification -
not a silently dropped distinction.
"""

from datetime import datetime
from typing import Any

from app.brokers.errors import MappingError
from app.brokers.models import BrokerHolding, BrokerPosition, BrokerProfile
from app.paper_trading.models import Order, OrderStatus
from app.trading.strategy.models import StrategyDirection

_KITE_STATUS_TO_INTERNAL: dict[str, OrderStatus] = {
    "COMPLETE": OrderStatus.FILLED,
    "REJECTED": OrderStatus.REJECTED,
    "CANCELLED": OrderStatus.CANCELLED,
    "OPEN": OrderStatus.SUBMITTED,
    "TRIGGER PENDING": OrderStatus.SUBMITTED,
    "OPEN PENDING": OrderStatus.SUBMITTED,
    "VALIDATION PENDING": OrderStatus.SUBMITTED,
    "MODIFY PENDING": OrderStatus.SUBMITTED,
    "CANCEL PENDING": OrderStatus.SUBMITTED,
    "PUT ORDER REQ RECEIVED": OrderStatus.SUBMITTED,
    "AMO REQ RECEIVED": OrderStatus.SUBMITTED,
}

_DIRECTION_TO_TRANSACTION_TYPE: dict[StrategyDirection, str] = {
    StrategyDirection.LONG: "BUY",
    StrategyDirection.SHORT: "SELL",
}

_TRANSACTION_TYPE_TO_DIRECTION: dict[str, StrategyDirection] = {
    "BUY": StrategyDirection.LONG,
    "SELL": StrategyDirection.SHORT,
}


def _require(payload: dict[str, Any], key: str, source: str) -> Any:
    if key not in payload:
        raise MappingError(f"{source} payload missing required field {key!r}: {payload!r}")
    return payload[key]


def map_order_status(kite_status: str) -> OrderStatus:
    mapped = _KITE_STATUS_TO_INTERNAL.get(kite_status)
    if mapped is None:
        raise MappingError(f"unrecognized Kite order status: {kite_status!r}")
    return mapped


def map_transaction_type(direction: StrategyDirection) -> str:
    mapped = _DIRECTION_TO_TRANSACTION_TYPE.get(direction)
    if mapped is None:
        raise MappingError(f"cannot place a Kite order for direction {direction!r}")
    return mapped


def map_direction(transaction_type: str) -> StrategyDirection:
    mapped = _TRANSACTION_TYPE_TO_DIRECTION.get(transaction_type)
    if mapped is None:
        raise MappingError(f"unrecognized Kite transaction_type: {transaction_type!r}")
    return mapped


def build_kite_order_request(
    order: Order,
    *,
    trading_symbol: str,
    exchange: str,
    product: str,
    order_type: str,
    variety: str,
) -> dict[str, Any]:
    """Internal `Order` -> the kwargs `KiteConnectClient.place_order()` expects."""
    request: dict[str, Any] = {
        "variety": variety,
        "exchange": exchange,
        "tradingsymbol": trading_symbol,
        "transaction_type": map_transaction_type(order.direction),
        "quantity": order.requested_quantity,
        "product": product,
        "order_type": order_type,
    }
    if order_type == "LIMIT":
        request["price"] = order.requested_price
    return request


def map_kite_order_update(original: Order, kite_order: dict[str, Any]) -> Order:
    """
    Merges a Kite order-history entry onto the internal `Order` that
    produced it - `strategy_name`/`stop_loss`/`target`/`requested_*`
    come from `original` (Kite's response doesn't carry them); status/
    fill data comes from `kite_order`.
    """
    status = map_order_status(str(_require(kite_order, "status", "Kite order")))
    filled_quantity = int(_require(kite_order, "filled_quantity", "Kite order"))
    average_price = kite_order.get("average_price")

    update: dict[str, Any] = {
        "status": status,
        "filled_quantity": filled_quantity,
        "average_fill_price": float(average_price) if average_price else None,
        "updated_at": datetime.now(),
    }
    if status == OrderStatus.REJECTED:
        update["rejection_reason"] = kite_order.get("status_message") or "rejected by broker"

    return original.model_copy(update=update)


def map_kite_position(kite_position: dict[str, Any]) -> BrokerPosition:
    try:
        return BrokerPosition(
            trading_symbol=_require(kite_position, "tradingsymbol", "Kite position"),
            exchange=_require(kite_position, "exchange", "Kite position"),
            product=_require(kite_position, "product", "Kite position"),
            quantity=int(_require(kite_position, "quantity", "Kite position")),
            average_price=float(_require(kite_position, "average_price", "Kite position")),
            last_price=float(_require(kite_position, "last_price", "Kite position")),
            pnl=float(_require(kite_position, "pnl", "Kite position")),
        )
    except (TypeError, ValueError) as exc:
        raise MappingError(f"malformed Kite position payload: {kite_position!r}") from exc


def map_kite_holding(kite_holding: dict[str, Any]) -> BrokerHolding:
    try:
        return BrokerHolding(
            trading_symbol=_require(kite_holding, "tradingsymbol", "Kite holding"),
            exchange=_require(kite_holding, "exchange", "Kite holding"),
            isin=_require(kite_holding, "isin", "Kite holding"),
            quantity=int(_require(kite_holding, "quantity", "Kite holding")),
            average_price=float(_require(kite_holding, "average_price", "Kite holding")),
            last_price=float(_require(kite_holding, "last_price", "Kite holding")),
            pnl=float(_require(kite_holding, "pnl", "Kite holding")),
        )
    except (TypeError, ValueError) as exc:
        raise MappingError(f"malformed Kite holding payload: {kite_holding!r}") from exc


def map_kite_profile(kite_profile: dict[str, Any]) -> BrokerProfile:
    try:
        return BrokerProfile(
            user_id=_require(kite_profile, "user_id", "Kite profile"),
            user_name=_require(kite_profile, "user_name", "Kite profile"),
            email=_require(kite_profile, "email", "Kite profile"),
            broker=_require(kite_profile, "broker", "Kite profile"),
        )
    except (TypeError, ValueError) as exc:
        raise MappingError(f"malformed Kite profile payload: {kite_profile!r}") from exc
