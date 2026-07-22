"""
NotificationService: the one place that decides whether/how a message
actually reaches Telegram. Never raises - a failed or disabled
notification must never interrupt signal processing, the same
"safety over completeness" discipline `app.live.safety_manager`
already established. When `NotificationConfig.enabled` is `False`
(the default), every `send_*` call is a no-op that only logs - no
network access of any kind.
"""

import logging

from app.notifications.message_formatter import (
    format_critical_error_message,
    format_daily_summary_message,
    format_exit_message,
    format_no_trade_message,
    format_runtime_event_message,
    format_signal_message,
)
from app.notifications.models import NotificationConfig, NotificationType
from app.notifications.telegram_client import TelegramClientInterface
from app.signals.models import DailyPerformanceReport, DummyTrade, GuardianScore, SignalType

logger = logging.getLogger(__name__)

_SIGNAL_TYPE_TO_NOTIFICATION_TYPE: dict[SignalType, NotificationType] = {
    SignalType.BUY_CE: NotificationType.BUY_CE,
    SignalType.BUY_PE: NotificationType.BUY_PE,
    SignalType.TARGET_HIT: NotificationType.TARGET_HIT,
    SignalType.STOPLOSS_HIT: NotificationType.STOPLOSS_HIT,
    SignalType.NO_TRADE: NotificationType.NO_TRADE,
}


class NotificationService:
    def __init__(self, *, config: NotificationConfig, client: TelegramClientInterface) -> None:
        self._config = config
        self._client = client
        self.sent_log: list[tuple[NotificationType, str]] = []

    def send_signal(self, signal_type: SignalType, trade: DummyTrade) -> None:
        self._send(
            _SIGNAL_TYPE_TO_NOTIFICATION_TYPE[signal_type],
            format_signal_message(signal_type, trade),
        )

    def send_exit(self, signal_type: SignalType, trade: DummyTrade) -> None:
        self._send(
            _SIGNAL_TYPE_TO_NOTIFICATION_TYPE[signal_type],
            format_exit_message(signal_type, trade),
        )

    def send_no_trade(self, guardian_score: GuardianScore, reason: str) -> None:
        self._send(NotificationType.NO_TRADE, format_no_trade_message(guardian_score, reason))

    def send_daily_summary(self, report: DailyPerformanceReport) -> None:
        self._send(NotificationType.DAILY_SUMMARY, format_daily_summary_message(report))

    def send_critical_error(self, message: str) -> None:
        self._send(NotificationType.CRITICAL_ERROR, format_critical_error_message(message))

    def send_runtime_started(self) -> None:
        self._send(NotificationType.RUNTIME_STARTED, format_runtime_event_message(started=True))

    def send_runtime_stopped(self) -> None:
        self._send(NotificationType.RUNTIME_STOPPED, format_runtime_event_message(started=False))

    def _send(self, notification_type: NotificationType, message: str) -> None:
        self.sent_log.append((notification_type, message))

        if not self._config.enabled:
            logger.info("NotificationService[%s] (disabled): %s", notification_type, message)
            return

        try:
            sent = self._client.send_message(message)
        except Exception:
            logger.exception("NotificationService[%s]: failed to send", notification_type)
            return

        if not sent:
            logger.warning("NotificationService[%s]: Telegram reported failure", notification_type)
