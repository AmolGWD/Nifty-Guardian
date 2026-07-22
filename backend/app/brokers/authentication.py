"""
Credential loading and session validation for the Zerodha broker
adapter - deliberately independent of `app.kite`'s OAuth login-flow/
session database (`app.kite.service.KiteAuthService`,
`app.kite.repository.KiteSessionRepository`). That machinery serves a
different concern - a human logging in through a browser to browse
market data - while this adapter is driven by an already-generated
access token supplied via environment variables, matching how
automated trading systems actually use Kite Connect day to day: a
human (or a scheduled job) completes the login flow once each morning
and feeds the resulting access token to this process as
`ZERODHA_ACCESS_TOKEN`, rather than this adapter performing an
interactive login itself.

Zerodha Kite Connect has no refresh-token concept - access tokens are
valid for a single trading day and can only be renewed by a fresh
login (request_token exchange), never silently refreshed.
`refresh_token` below is included because the CTO brief names it
("Refresh Token (if applicable)") - it is honestly documented as
unused rather than faked with a mechanism Kite's real API doesn't have.
"""

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.brokers.errors import AuthenticationError
from app.brokers.interface import KiteConnectClient
from app.brokers.mapper import map_kite_profile
from app.brokers.models import BrokerProfile


class ZerodhaCredentials(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="ZERODHA_", env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    api_key: str = ""
    api_secret: str = ""
    access_token: str = ""
    base_url: str | None = None
    # Honest placeholder - see module docstring. Kite Connect has no
    # refresh-token mechanism; this is never read by anything.
    refresh_token: str | None = None

    @model_validator(mode="after")
    def _validate(self) -> "ZerodhaCredentials":
        missing = [
            name
            for name, value in (
                ("ZERODHA_API_KEY", self.api_key),
                ("ZERODHA_API_SECRET", self.api_secret),
                ("ZERODHA_ACCESS_TOKEN", self.access_token),
            )
            if not value
        ]
        if missing:
            raise AuthenticationError(
                f"missing required environment variable(s): {', '.join(missing)}"
            )
        return self


def load_credentials() -> ZerodhaCredentials:
    """
    Loads `ZERODHA_API_KEY`/`ZERODHA_API_SECRET`/`ZERODHA_ACCESS_TOKEN`/
    `ZERODHA_BASE_URL` from the environment (or `.env`, for local dev
    parity with `app.core.config.Settings`'s own convention) - never
    hardcoded. Raises `AuthenticationError` immediately if any required
    value is missing, rather than deferring the failure to the first
    API call.
    """
    try:
        return ZerodhaCredentials()
    except AuthenticationError:
        raise
    except Exception as exc:  # pydantic-settings validation errors, malformed env values
        raise AuthenticationError(f"invalid Zerodha credentials: {exc}") from exc


def validate_session(client: KiteConnectClient) -> BrokerProfile:
    """
    Confirms the configured access token is actually valid by making
    the cheapest authenticated call Kite Connect offers (`profile()`)
    - `kite_client.py`'s exception translation already turns an
    expired/invalid token into `AuthenticationError` for any call, this
    just does so eagerly and predictably, rather than waiting for
    whichever call happens to run first.
    """
    return map_kite_profile(client.profile())
