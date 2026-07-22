import pytest

from app.brokers.authentication import load_credentials, validate_session
from app.brokers.errors import AuthenticationError
from tests.brokers.helpers import FakeKiteConnectClient


@pytest.fixture
def clean_zerodha_env(monkeypatch: pytest.MonkeyPatch) -> None:
    names = ("ZERODHA_API_KEY", "ZERODHA_API_SECRET", "ZERODHA_ACCESS_TOKEN", "ZERODHA_BASE_URL")
    for name in names:
        monkeypatch.delenv(name, raising=False)


def test_load_credentials_raises_when_everything_is_missing(clean_zerodha_env: None) -> None:
    with pytest.raises(AuthenticationError, match="ZERODHA_API_KEY"):
        load_credentials()


def test_load_credentials_raises_naming_every_missing_variable(
    clean_zerodha_env: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("ZERODHA_API_KEY", "key123")
    with pytest.raises(AuthenticationError) as exc_info:
        load_credentials()
    assert "ZERODHA_API_SECRET" in str(exc_info.value)
    assert "ZERODHA_ACCESS_TOKEN" in str(exc_info.value)
    assert "ZERODHA_API_KEY" not in str(exc_info.value)


def test_load_credentials_succeeds_when_all_required_vars_present(
    clean_zerodha_env: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("ZERODHA_API_KEY", "key123")
    monkeypatch.setenv("ZERODHA_API_SECRET", "secret123")
    monkeypatch.setenv("ZERODHA_ACCESS_TOKEN", "token123")

    credentials = load_credentials()

    assert credentials.api_key == "key123"
    assert credentials.api_secret == "secret123"
    assert credentials.access_token == "token123"
    assert credentials.base_url is None


def test_load_credentials_reads_optional_base_url(
    clean_zerodha_env: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("ZERODHA_API_KEY", "key123")
    monkeypatch.setenv("ZERODHA_API_SECRET", "secret123")
    monkeypatch.setenv("ZERODHA_ACCESS_TOKEN", "token123")
    monkeypatch.setenv("ZERODHA_BASE_URL", "https://api.kite.trade")

    credentials = load_credentials()

    assert credentials.base_url == "https://api.kite.trade"


def test_load_credentials_never_hardcodes_a_default_token(
    clean_zerodha_env: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("ZERODHA_API_KEY", "key123")
    monkeypatch.setenv("ZERODHA_API_SECRET", "secret123")
    monkeypatch.setenv("ZERODHA_ACCESS_TOKEN", "token123")

    credentials = load_credentials()

    assert credentials.refresh_token is None


def test_validate_session_calls_profile_and_maps_it() -> None:
    client = FakeKiteConnectClient(
        profile_response={
            "user_id": "AB1234",
            "user_name": "Test User",
            "email": "test@example.com",
            "broker": "ZERODHA",
        }
    )

    profile = validate_session(client)

    assert profile.user_id == "AB1234"
    assert profile.broker == "ZERODHA"
