import pytest

from app.brokers.errors import MappingError
from app.brokers.mapper import (
    build_kite_order_request,
    map_direction,
    map_kite_holding,
    map_kite_order_update,
    map_kite_position,
    map_kite_profile,
    map_order_status,
    map_transaction_type,
)
from app.paper_trading.models import OrderStatus
from app.trading.strategy.models import StrategyDirection
from tests.brokers.helpers import make_order


@pytest.mark.parametrize(
    ("kite_status", "expected"),
    [
        ("COMPLETE", OrderStatus.FILLED),
        ("REJECTED", OrderStatus.REJECTED),
        ("CANCELLED", OrderStatus.CANCELLED),
        ("OPEN", OrderStatus.SUBMITTED),
        ("TRIGGER PENDING", OrderStatus.SUBMITTED),
        ("VALIDATION PENDING", OrderStatus.SUBMITTED),
        ("AMO REQ RECEIVED", OrderStatus.SUBMITTED),
    ],
)
def test_map_order_status(kite_status: str, expected: OrderStatus) -> None:
    assert map_order_status(kite_status) == expected


def test_map_order_status_rejects_unrecognized_value() -> None:
    with pytest.raises(MappingError, match="unrecognized Kite order status"):
        map_order_status("SOME_NEW_KITE_STATUS")


@pytest.mark.parametrize(
    ("direction", "expected"),
    [(StrategyDirection.LONG, "BUY"), (StrategyDirection.SHORT, "SELL")],
)
def test_map_transaction_type(direction: StrategyDirection, expected: str) -> None:
    assert map_transaction_type(direction) == expected


def test_map_transaction_type_rejects_none_direction() -> None:
    with pytest.raises(MappingError):
        map_transaction_type(StrategyDirection.NONE)


@pytest.mark.parametrize(
    ("transaction_type", "expected"),
    [("BUY", StrategyDirection.LONG), ("SELL", StrategyDirection.SHORT)],
)
def test_map_direction(transaction_type: str, expected: StrategyDirection) -> None:
    assert map_direction(transaction_type) == expected


def test_map_direction_rejects_unrecognized_value() -> None:
    with pytest.raises(MappingError):
        map_direction("SHORT_SELL")


def test_build_kite_order_request_market_order_has_no_price() -> None:
    order = make_order()
    request = build_kite_order_request(
        order,
        trading_symbol="NIFTY24JULFUT",
        exchange="NFO",
        product="MIS",
        order_type="MARKET",
        variety="regular",
    )
    assert request["tradingsymbol"] == "NIFTY24JULFUT"
    assert request["transaction_type"] == "BUY"
    assert request["quantity"] == 50
    assert "price" not in request


def test_build_kite_order_request_limit_order_includes_price() -> None:
    order = make_order(requested_price=151.25)
    request = build_kite_order_request(
        order,
        trading_symbol="NIFTY24JULFUT",
        exchange="NFO",
        product="MIS",
        order_type="LIMIT",
        variety="regular",
    )
    assert request["price"] == 151.25


def test_map_kite_order_update_merges_status_and_fill_onto_original() -> None:
    order = make_order()
    updated = map_kite_order_update(
        order, {"status": "COMPLETE", "filled_quantity": 50, "average_price": 152.5}
    )
    assert updated.status == OrderStatus.FILLED
    assert updated.filled_quantity == 50
    assert updated.average_fill_price == 152.5
    # Fields Kite doesn't carry are preserved from the original.
    assert updated.strategy_name == order.strategy_name
    assert updated.stop_loss == order.stop_loss
    assert updated.target == order.target


def test_map_kite_order_update_sets_rejection_reason_when_rejected() -> None:
    order = make_order()
    updated = map_kite_order_update(
        order,
        {
            "status": "REJECTED",
            "filled_quantity": 0,
            "average_price": None,
            "status_message": "insufficient margin",
        },
    )
    assert updated.status == OrderStatus.REJECTED
    assert updated.rejection_reason == "insufficient margin"


def test_map_kite_order_update_missing_field_raises_mapping_error() -> None:
    order = make_order()
    with pytest.raises(MappingError):
        map_kite_order_update(order, {"filled_quantity": 0})


def test_map_kite_position() -> None:
    position = map_kite_position(
        {
            "tradingsymbol": "NIFTY24JULFUT",
            "exchange": "NFO",
            "product": "MIS",
            "quantity": 50,
            "average_price": 150.0,
            "last_price": 152.5,
            "pnl": 125.0,
        }
    )
    assert position.trading_symbol == "NIFTY24JULFUT"
    assert position.pnl == 125.0


def test_map_kite_position_malformed_raises_mapping_error() -> None:
    with pytest.raises(MappingError):
        map_kite_position({"tradingsymbol": "NIFTY24JULFUT"})


def test_map_kite_holding() -> None:
    holding = map_kite_holding(
        {
            "tradingsymbol": "INFY",
            "exchange": "NSE",
            "isin": "INE009A01021",
            "quantity": 10,
            "average_price": 1500.0,
            "last_price": 1550.0,
            "pnl": 500.0,
        }
    )
    assert holding.isin == "INE009A01021"
    assert holding.pnl == 500.0


def test_map_kite_holding_malformed_raises_mapping_error() -> None:
    with pytest.raises(MappingError):
        map_kite_holding({"tradingsymbol": "INFY"})


def test_map_kite_profile() -> None:
    profile = map_kite_profile(
        {
            "user_id": "AB1234",
            "user_name": "Test User",
            "email": "t@example.com",
            "broker": "ZERODHA",
        }
    )
    assert profile.user_id == "AB1234"
    assert profile.broker == "ZERODHA"


def test_map_kite_profile_malformed_raises_mapping_error() -> None:
    with pytest.raises(MappingError):
        map_kite_profile({"user_id": "AB1234"})
