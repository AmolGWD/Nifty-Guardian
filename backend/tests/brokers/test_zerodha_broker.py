import pytest

from app.brokers.errors import MappingError
from app.brokers.zerodha_broker import ZerodhaBroker
from app.paper_trading.broker_interface import BrokerInterface
from app.paper_trading.models import OrderStatus
from tests.brokers.helpers import FakeKiteConnectClient, make_order


def test_zerodha_broker_satisfies_broker_interface() -> None:
    """
    `BrokerInterface` (frozen, app.paper_trading) is a plain `Protocol`,
    not `@runtime_checkable` - `isinstance()` against it always raises,
    so structural compliance is what mypy already verifies via this
    exact assignment (a `ZerodhaBroker` assigned to a `BrokerInterface`-
    typed variable fails mypy if the shape doesn't match). This test
    additionally confirms the two required methods exist and are
    callable, as a runtime backstop.
    """
    client = FakeKiteConnectClient()
    broker: BrokerInterface = ZerodhaBroker(
        client, trading_symbol_resolver=lambda order: "NIFTY24JULFUT"
    )
    assert callable(broker.submit_order)
    assert callable(broker.cancel_order)


def test_submit_order_places_and_refreshes_from_history() -> None:
    client = FakeKiteConnectClient(
        placed_order_id="KITE0001",
        order_history_response=[
            {"status": "COMPLETE", "filled_quantity": 50, "average_price": 152.5}
        ],
    )
    broker = ZerodhaBroker(client, trading_symbol_resolver=lambda order: "NIFTY24JULFUT")
    order = make_order()

    result = broker.submit_order(order)

    assert result.order_id == "KITE0001"
    assert result.status == OrderStatus.FILLED
    assert result.filled_quantity == 50
    assert result.average_fill_price == 152.5
    # Fields the broker doesn't carry are preserved from the original order.
    assert result.strategy_name == order.strategy_name
    assert result.stop_loss == order.stop_loss


def test_submit_order_uses_configured_defaults_and_direction() -> None:
    client = FakeKiteConnectClient()
    broker = ZerodhaBroker(
        client,
        default_exchange="NFO",
        default_product="MIS",
        default_order_type="MARKET",
        default_variety="regular",
        trading_symbol_resolver=lambda order: "NIFTY24JULFUT",
    )
    broker.submit_order(make_order())

    assert len(client.place_order_calls) == 1
    call = client.place_order_calls[0]
    assert call["exchange"] == "NFO"
    assert call["product"] == "MIS"
    assert call["order_type"] == "MARKET"
    assert call["variety"] == "regular"
    assert call["transaction_type"] == "BUY"
    assert call["tradingsymbol"] == "NIFTY24JULFUT"


def test_submit_order_without_a_resolver_raises_mapping_error() -> None:
    broker = ZerodhaBroker(FakeKiteConnectClient())
    with pytest.raises(MappingError, match="no trading_symbol_resolver configured"):
        broker.submit_order(make_order())


def test_cancel_order_refreshes_from_history() -> None:
    client = FakeKiteConnectClient(
        order_history_response=[
            {"status": "CANCELLED", "filled_quantity": 0, "average_price": None}
        ]
    )
    broker = ZerodhaBroker(client, trading_symbol_resolver=lambda order: "NIFTY24JULFUT")
    order = make_order(order_id="KITE0001", status=OrderStatus.SUBMITTED)

    result = broker.cancel_order(order)

    assert result.status == OrderStatus.CANCELLED
    assert client.cancel_order_calls == [{"variety": "regular", "order_id": "KITE0001"}]


def test_refresh_order_raises_mapping_error_on_empty_history() -> None:
    client = FakeKiteConnectClient(order_history_response=[])
    broker = ZerodhaBroker(client, trading_symbol_resolver=lambda order: "NIFTY24JULFUT")

    with pytest.raises(MappingError, match="no order history"):
        broker.submit_order(make_order())


def test_get_positions_maps_net_positions() -> None:
    client = FakeKiteConnectClient(
        positions_response={
            "net": [
                {
                    "tradingsymbol": "NIFTY24JULFUT",
                    "exchange": "NFO",
                    "product": "MIS",
                    "quantity": 50,
                    "average_price": 150.0,
                    "last_price": 152.5,
                    "pnl": 125.0,
                }
            ]
        }
    )
    broker = ZerodhaBroker(client)

    positions = broker.get_positions()

    assert len(positions) == 1
    assert positions[0].trading_symbol == "NIFTY24JULFUT"


def test_get_holdings_maps_every_holding() -> None:
    client = FakeKiteConnectClient(
        holdings_response=[
            {
                "tradingsymbol": "INFY",
                "exchange": "NSE",
                "isin": "INE009A01021",
                "quantity": 10,
                "average_price": 1500.0,
                "last_price": 1550.0,
                "pnl": 500.0,
            }
        ]
    )
    broker = ZerodhaBroker(client)

    holdings = broker.get_holdings()

    assert len(holdings) == 1
    assert holdings[0].isin == "INE009A01021"


def test_get_profile_returns_mapped_profile() -> None:
    client = FakeKiteConnectClient(
        profile_response={
            "user_id": "AB1234",
            "user_name": "Test User",
            "email": "test@example.com",
            "broker": "ZERODHA",
        }
    )
    broker = ZerodhaBroker(client)

    profile = broker.get_profile()

    assert profile.user_id == "AB1234"
    assert profile.broker == "ZERODHA"
