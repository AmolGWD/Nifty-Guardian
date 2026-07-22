"""
Typed exceptions this adapter raises - never a raw `kiteconnect`
exception, never a bare `Exception`. `kite_client.py` is the one place
that catches `kiteconnect.exceptions.KiteException` (and subclasses)
and translates them into one of these via `translate_kite_exception()`
- nothing outside this package should ever need to import
`kiteconnect.exceptions`.
"""


class BrokerError(Exception):
    """Base class for every exception this package raises."""


class AuthenticationError(BrokerError):
    """Missing/invalid credentials, an expired access token, or insufficient permissions."""


class ConnectionError(BrokerError):  # shadows the builtin, intentionally - matches the CTO brief
    """The broker's API could not be reached (network failure, DNS, connection refused)."""


class OrderRejectedError(BrokerError):
    """The broker rejected an order/cancellation outright (bad quantity, insufficient margin)."""


class RateLimitError(BrokerError):
    """The broker's API returned a rate-limit response (HTTP 429)."""


class BrokerUnavailableError(BrokerError):
    """The broker's API responded, but with a general/server-side failure, not one of the above."""


class MappingError(BrokerError):
    """
    This adapter's own request/response translation failed - a Kite
    payload had a shape this adapter didn't expect, or an internal
    `Order` was missing data (e.g. no trading symbol resolver
    configured) this adapter needs to build a real broker request.
    Never a broker-side failure - always this package's own mapping
    layer refusing to guess.
    """
