"""
NotificationService: the one place that decides whether/how a message
actually reaches Telegram. Never raises - a failed or disabled
notification must never interrupt signal processing, the same
"safety over completeness" discipline `app.live.safety_manager`
already established. When `NotificationConfig.enabled` is `False`
(the default), every `send_*` call is a no-op that only logs - no
network access of any kind.

Retry: a failed send is retried up to `config.retry_count` additional
times, waiting `config.retry_delay` seconds between attempts - both
configuration-driven (`TELEGRAM_RETRY_COUNT`/`TELEGRAM_RETRY_DELAY`).
Exhausting all retries is logged and recorded via `last_status`
(`TelegramStatus.FAILED`) - never raised, never crashes the caller.

Duplicate prevention: `send_signal()` is keyed by the `DummyTrade`'s
own `trade_id` - a second call for a trade already notified is a
no-op. This is a notification-layer-only safeguard (the Signal Engine
itself already only calls `send_signal()` once per accepted signal,
per its own `SignalFilter`); it exists so "never resend the same
signal" is guaranteed here too, independent of the caller.
"""

import logging
import time

from app.notifications.message_formatter import (
    format_critical_error_message,
    format_daily_summary_message,
    format_exit_message,
    format_no_trade_message,
    format_runtime_event_message,
    format_signal_message,
)
from app.notifications.models import NotificationConfig, NotificationType, TelegramStatus
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
        self._notified_trade_ids: set[str] = set()
        self.last_status: TelegramStatus | None = None

    def send_signal(self, signal_type: SignalType, trade: DummyTrade) -> None:
        if trade.trade_id in self._notified_trade_ids:
            logger.info(
                "NotificationService: duplicate signal for trade %s suppressed - already notified",
                trade.trade_id,
            )
            return
        self._notified_trade_ids.add(trade.trade_id)
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

        attempts = self._config.retry_count + 1
        for attempt in range(1, attempts + 1):
            try:
                sent = self._client.send_message(message)
            except Exception:
                logger.exception(
                    "NotificationService[%s]: send attempt %d/%d raised",
                    notification_type, attempt, attempts,
                )
                sent = False

            if sent:
                self.last_status = TelegramStatus.SENT
                return

            logger.warning(
                "NotificationService[%s]: send attempt %d/%d failed",
                notification_type, attempt, attempts,
            )
            if attempt < attempts:
                time.sleep(self._config.retry_delay)

        self.last_status = TelegramStatus.FAILED
        logger.error(
            "NotificationService[%s]: exhausted %d attempt(s) - giving up, Guardian continues",
            notification_type, attempts,
        )
