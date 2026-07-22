"""
Startup validation: catches configuration mistakes that would
otherwise only surface once something actually goes wrong in
production - an empty Zerodha credential with `LIVE_MODE=true`, DEBUG
logging left on, a CORS origin still pointed at localhost. Every check
here is read-only against already-loaded settings; nothing here
mutates `app.core.config.Settings`, `app.live.models.LiveConfig`, or
`app.brokers.authentication.ZerodhaCredentials` (all frozen) - it only
inspects them and reports what it finds.
"""

import logging
import os
from typing import Literal

from pydantic import BaseModel, ConfigDict

from app.core.config import Settings
from app.live.models import LiveConfig
from app.observability.diagnostics import get_app_metadata

logger = logging.getLogger(__name__)

_KNOWN_ENVIRONMENTS = frozenset({"development", "staging", "production"})


class StartupIssue(BaseModel):
    model_config = ConfigDict(frozen=True)

    level: Literal["warning", "error"]
    message: str


def validate_startup(
    settings: Settings,
    *,
    live_config: LiveConfig | None = None,
) -> list[StartupIssue]:
    """Returns every configuration issue found - never raises. Callers decide what to do."""
    issues: list[StartupIssue] = []
    live_config = live_config or LiveConfig()

    if settings.environment not in _KNOWN_ENVIRONMENTS:
        issues.append(
            StartupIssue(
                level="warning",
                message=(
                    f"ENVIRONMENT={settings.environment!r} is not one of "
                    f"{sorted(_KNOWN_ENVIRONMENTS)} - defaults tuned for known "
                    f"environments may not apply"
                ),
            )
        )

    if settings.environment == "production":
        if settings.log_level.upper() == "DEBUG":
            issues.append(
                StartupIssue(
                    level="warning",
                    message="LOG_LEVEL=DEBUG in production is too verbose; use INFO or higher",
                )
            )
        if any("localhost" in origin for origin in settings.cors_origins_list):
            issues.append(
                StartupIssue(
                    level="warning",
                    message="CORS_ORIGINS includes a localhost origin in production",
                )
            )
        if len(settings.secret_key) < 32:
            issues.append(
                StartupIssue(
                    level="error",
                    message="SECRET_KEY is shorter than expected for a generated Fernet key",
                )
            )

    if live_config.live_mode and not (
        os.environ.get("ZERODHA_API_KEY") and os.environ.get("ZERODHA_ACCESS_TOKEN")
    ):
        issues.append(
            StartupIssue(
                level="error",
                message="LIVE_MODE=true but ZERODHA_API_KEY/ZERODHA_ACCESS_TOKEN are not both set",
            )
        )

    return issues


def run_startup_diagnostics(settings: Settings) -> list[StartupIssue]:
    """Logs app metadata at INFO and every validation issue at WARNING/ERROR; returns the issues."""
    metadata = get_app_metadata(app_name=settings.app_name, environment=settings.environment)
    logger.info(
        "startup: %s v%s (environment=%s, git_commit=%s, python=%s)",
        metadata.name,
        metadata.version,
        metadata.environment,
        metadata.git_commit,
        metadata.python_version,
    )

    issues = validate_startup(settings)
    for issue in issues:
        level = logging.ERROR if issue.level == "error" else logging.WARNING
        logger.log(level, "startup validation [%s]: %s", issue.level, issue.message)

    if not issues:
        logger.info("startup validation: no issues found")

    return issues
