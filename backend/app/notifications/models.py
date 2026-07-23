"""
Configuration and message-type enum for the Telegram integration.
`NotificationConfig.telegram_enabled` defaults to `False` - the same
safe-default discipline `app.live.models.LiveConfig.live_mode` already
established: nothing is ever sent anywhere until an operator
explicitly opts in.
"""

from enum import StrEnum

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class NotificationType(StrEnum):
    BUY_CE = "BuyCE"
    BUY_PE = "BuyPE"
    TARGET_HIT = "TargetHit"
    STOPLOSS_HIT = "StoplossHit"
    NO_TRADE = "NoTrade"
    DAILY_SUMMARY = "DailySummary"
    CRITICAL_ERROR = "CriticalError"
    RUNTIME_STARTED = "RuntimeStarted"
    RUNTIME_STOPPED = "RuntimeStopped"


class TelegramStatus(StrEnum):
    SENT = "Sent"
    FAILED = "Failed"


class NotificationConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="TELEGRAM_", env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    enabled: bool = False
    bot_token: str = ""
    chat_id: str = ""
    # How many times to retry a failed send (0 = try once, never retry) and
    # how long to wait between attempts - both configuration-driven, per
    # the CTO brief, rather than a hardcoded backoff policy.
    retry_count: int = 3
    retry_delay: float = 2.0

    @field_validator("retry_count")
    @classmethod
    def _validate_retry_count(cls, value: int) -> int:
        if value < 0:
            raise ValueError("retry_count must be >= 0")
        return value

    @field_validator("retry_delay")
    @classmethod
    def _validate_retry_delay(cls, value: float) -> float:
        if value < 0:
            raise ValueError("retry_delay must be >= 0")
        return value
