"""
Configuration and message-type enum for the Telegram integration.
`NotificationConfig.telegram_enabled` defaults to `False` - the same
safe-default discipline `app.live.models.LiveConfig.live_mode` already
established: nothing is ever sent anywhere until an operator
explicitly opts in.
"""

from enum import StrEnum

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


class NotificationConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="TELEGRAM_", env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    enabled: bool = False
    bot_token: str = ""
    chat_id: str = ""
