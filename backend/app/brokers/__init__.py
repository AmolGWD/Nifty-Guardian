"""
Zerodha Broker Adapter (Phase 23) - implements
`app.paper_trading.broker_interface.BrokerInterface` (frozen) so a
live Zerodha connection can plug into the same `OrderManager` that
already drives `PaperBroker` (frozen, untouched). Broker connectivity
only: no new trading logic, no changes to app.runtime or app.trading.
See docs/ZERODHA_ADAPTER_GUIDE.md.
"""

from app.brokers.authentication import ZerodhaCredentials, load_credentials, validate_session
from app.brokers.errors import (
    AuthenticationError,
    BrokerError,
    BrokerUnavailableError,
    ConnectionError,
    MappingError,
    OrderRejectedError,
    RateLimitError,
)
from app.brokers.interface import KiteConnectClient
from app.brokers.kite_client import (
    ZerodhaKiteClient,
    build_kite_connect_client,
    translate_kite_exception,
)
from app.brokers.models import BrokerHolding, BrokerOrder, BrokerPosition, BrokerProfile
from app.brokers.zerodha_broker import ZerodhaBroker, build_zerodha_broker

__all__ = [
    "AuthenticationError",
    "BrokerError",
    "BrokerHolding",
    "BrokerOrder",
    "BrokerPosition",
    "BrokerProfile",
    "BrokerUnavailableError",
    "ConnectionError",
    "KiteConnectClient",
    "MappingError",
    "OrderRejectedError",
    "RateLimitError",
    "ZerodhaBroker",
    "ZerodhaCredentials",
    "ZerodhaKiteClient",
    "build_kite_connect_client",
    "build_zerodha_broker",
    "load_credentials",
    "translate_kite_exception",
    "validate_session",
]
