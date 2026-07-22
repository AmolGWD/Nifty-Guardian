import pytest
from kiteconnect.exceptions import (
    DataException,
    GeneralException,
    InputException,
    NetworkException,
    OrderException,
    PermissionException,
    TokenException,
)

from app.brokers.errors import (
    AuthenticationError,
    BrokerUnavailableError,
    MappingError,
    OrderRejectedError,
    RateLimitError,
)
from app.brokers.errors import (
    ConnectionError as BrokerConnectionError,
)
from app.brokers.kite_client import ZerodhaKiteClient, translate_kite_exception


@pytest.mark.parametrize(
    ("exc", "expected_type"),
    [
        (TokenException("invalid token", code=403), AuthenticationError),
        (PermissionException("insufficient permission", code=403), AuthenticationError),
        (NetworkException("connection refused", code=503), BrokerConnectionError),
        (OrderException("order rejected", code=400), OrderRejectedError),
        (InputException("bad input", code=400), MappingError),
        (GeneralException("server error", code=500), BrokerUnavailableError),
        (DataException("bad data", code=502), BrokerUnavailableError),
    ],
)
def test_translate_kite_exception_maps_each_category(exc: Exception, expected_type: type) -> None:
    assert isinstance(translate_kite_exception(exc), expected_type)


def test_translate_kite_exception_detects_rate_limit_by_status_code() -> None:
    exc = GeneralException("too many requests", code=429)
    assert isinstance(translate_kite_exception(exc), RateLimitError)


class _FakeKiteConnect:
    def __init__(self, *, raise_on: str | None = None, exc: Exception | None = None) -> None:
        self._raise_on = raise_on
        self._exc = exc

    def _maybe_raise(self, name: str) -> None:
        if self._raise_on == name:
            assert self._exc is not None
            raise self._exc

    def place_order(self, **kwargs: object) -> str:
        self._maybe_raise("place_order")
        return "KITE0001"

    def cancel_order(self, **kwargs: object) -> str:
        self._maybe_raise("cancel_order")
        return str(kwargs.get("order_id"))

    def order_history(self, order_id: str) -> list[dict[str, object]]:
        self._maybe_raise("order_history")
        return [{"status": "COMPLETE", "filled_quantity": 10, "average_price": 100.0}]

    def positions(self) -> dict[str, object]:
        self._maybe_raise("positions")
        return {"net": []}

    def holdings(self) -> list[dict[str, object]]:
        self._maybe_raise("holdings")
        return []

    def profile(self) -> dict[str, object]:
        self._maybe_raise("profile")
        return {
            "user_id": "AB1234",
            "user_name": "Test",
            "email": "t@example.com",
            "broker": "ZERODHA",
        }


def test_zerodha_kite_client_place_order_delegates_to_sdk() -> None:
    client = ZerodhaKiteClient(_FakeKiteConnect())
    order_id = client.place_order(
        variety="regular",
        exchange="NFO",
        tradingsymbol="NIFTY24JULFUT",
        transaction_type="BUY",
        quantity=50,
        product="MIS",
        order_type="MARKET",
    )
    assert order_id == "KITE0001"


def test_zerodha_kite_client_translates_sdk_exceptions() -> None:
    fake = _FakeKiteConnect(raise_on="place_order", exc=TokenException("expired", code=403))
    client = ZerodhaKiteClient(fake)

    with pytest.raises(AuthenticationError):
        client.place_order(
            variety="regular",
            exchange="NFO",
            tradingsymbol="NIFTY24JULFUT",
            transaction_type="BUY",
            quantity=50,
            product="MIS",
            order_type="MARKET",
        )


def test_zerodha_kite_client_cancel_order_translates_exceptions() -> None:
    fake = _FakeKiteConnect(raise_on="cancel_order", exc=OrderException("cannot cancel", code=400))
    client = ZerodhaKiteClient(fake)

    with pytest.raises(OrderRejectedError):
        client.cancel_order(variety="regular", order_id="KITE0001")


def test_zerodha_kite_client_positions_holdings_profile() -> None:
    client = ZerodhaKiteClient(_FakeKiteConnect())
    assert client.positions() == {"net": []}
    assert client.holdings() == []
    assert client.profile()["user_id"] == "AB1234"


def test_zerodha_kite_client_network_failure_on_holdings() -> None:
    fake = _FakeKiteConnect(raise_on="holdings", exc=NetworkException("timeout", code=503))
    client = ZerodhaKiteClient(fake)

    with pytest.raises(BrokerConnectionError):
        client.holdings()
