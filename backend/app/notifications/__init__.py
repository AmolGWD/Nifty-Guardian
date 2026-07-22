"""
Telegram notifications: BUY CE/BUY PE, TARGET HIT/STOPLOSS HIT, NO
TRADE, Daily Summary, Critical Errors, Runtime Started/Stopped.
Disabled by default (`TELEGRAM_ENABLED=false`) - no network access
until an operator explicitly opts in.
"""

from app.notifications.message_formatter import (
    format_critical_error_message,
    format_daily_summary_message,
    format_exit_message,
    format_no_trade_message,
    format_runtime_event_message,
    format_signal_message,
)
from app.notifications.models import NotificationConfig, NotificationType
from app.notifications.notification_service import NotificationService
from app.notifications.telegram_client import HttpTelegramClient, TelegramClientInterface

__all__ = [
    "HttpTelegramClient",
    "NotificationConfig",
    "NotificationService",
    "NotificationType",
    "TelegramClientInterface",
    "format_critical_error_message",
    "format_daily_summary_message",
    "format_exit_message",
    "format_no_trade_message",
    "format_runtime_event_message",
    "format_signal_message",
]
