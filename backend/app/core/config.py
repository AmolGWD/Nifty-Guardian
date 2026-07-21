"""
Application configuration.

All configuration is loaded from environment variables (via a local
.env file in development). Nothing here should be hardcoded per
environment - only sensible local-development defaults are provided,
and every value is overridable via the environment.
"""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "NIFTY Guardian v2"
    environment: str = "development"
    log_level: str = "INFO"

    host: str = "0.0.0.0"
    port: int = 8000

    cors_origins: str = "http://localhost:5173"

    database_url: str = f"sqlite:///{_BACKEND_DIR / 'data' / 'nifty_guardian.db'}"

    # Required - a Fernet key used to encrypt secrets (e.g. Kite access
    # tokens) at rest. Generate one with:
    #   python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
    # No default: the app should fail to start rather than silently
    # store secrets unencrypted or with a shared, guessable key.
    secret_key: str

    kite_api_key: str = ""
    kite_api_secret: str = ""

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
