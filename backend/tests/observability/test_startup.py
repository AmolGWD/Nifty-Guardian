from typing import Any

import pytest

from app.core.config import Settings
from app.live.models import LiveConfig
from app.observability.startup import validate_startup


def _settings(**overrides: Any) -> Settings:
    base: dict[str, Any] = dict(_env_file=None, secret_key="x" * 44)
    base.update(overrides)
    return Settings(**base)


def test_no_issues_for_a_normal_development_configuration() -> None:
    issues = validate_startup(_settings(environment="development"))
    assert issues == []


def test_unknown_environment_produces_a_warning() -> None:
    issues = validate_startup(_settings(environment="qa"))

    assert len(issues) == 1
    assert issues[0].level == "warning"
    assert "qa" in issues[0].message


def test_production_with_debug_logging_produces_a_warning() -> None:
    issues = validate_startup(_settings(environment="production", log_level="DEBUG"))

    assert any(i.level == "warning" and "LOG_LEVEL" in i.message for i in issues)


def test_production_with_localhost_cors_produces_a_warning() -> None:
    issues = validate_startup(
        _settings(environment="production", cors_origins="http://localhost:5173")
    )

    assert any(i.level == "warning" and "CORS_ORIGINS" in i.message for i in issues)


def test_production_with_short_secret_key_produces_an_error() -> None:
    issues = validate_startup(_settings(environment="production", secret_key="short"))

    assert any(i.level == "error" and "SECRET_KEY" in i.message for i in issues)


def test_production_with_a_proper_secret_key_has_no_secret_key_error() -> None:
    issues = validate_startup(
        _settings(environment="production", log_level="INFO", cors_origins="https://app.example.com")
    )

    assert not any("SECRET_KEY" in i.message for i in issues)


def test_live_mode_without_zerodha_credentials_produces_an_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("ZERODHA_API_KEY", raising=False)
    monkeypatch.delenv("ZERODHA_ACCESS_TOKEN", raising=False)

    issues = validate_startup(
        _settings(environment="development"), live_config=LiveConfig(_env_file=None, live_mode=True)
    )

    assert any(i.level == "error" and "LIVE_MODE" in i.message for i in issues)


def test_live_mode_with_zerodha_credentials_present_has_no_live_mode_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ZERODHA_API_KEY", "test-key")
    monkeypatch.setenv("ZERODHA_ACCESS_TOKEN", "test-token")

    issues = validate_startup(
        _settings(environment="development"), live_config=LiveConfig(_env_file=None, live_mode=True)
    )

    assert not any("LIVE_MODE" in i.message for i in issues)


def test_live_mode_false_never_checks_zerodha_credentials(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("ZERODHA_API_KEY", raising=False)
    monkeypatch.delenv("ZERODHA_ACCESS_TOKEN", raising=False)

    issues = validate_startup(
        _settings(environment="development"),
        live_config=LiveConfig(_env_file=None, live_mode=False),
    )

    assert not any("LIVE_MODE" in i.message for i in issues)
