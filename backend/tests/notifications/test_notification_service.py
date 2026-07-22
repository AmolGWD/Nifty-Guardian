from app.notifications.models import NotificationConfig, NotificationType
from app.notifications.notification_service import NotificationService
from app.signals.models import SignalType
from tests.notifications.helpers import make_closed_trade, make_open_trade, make_report, make_score


class FakeTelegramClient:
    def __init__(self, *, succeeds: bool = True) -> None:
        self.messages: list[str] = []
        self._succeeds = succeeds

    def send_message(self, text: str) -> bool:
        self.messages.append(text)
        return self._succeeds


def test_disabled_config_never_calls_the_client() -> None:
    client = FakeTelegramClient()
    service = NotificationService(
        config=NotificationConfig(enabled=False), client=client
    )

    service.send_signal(SignalType.BUY_CE, make_open_trade())

    assert client.messages == []
    assert service.sent_log[0][0] == NotificationType.BUY_CE


def test_enabled_config_sends_through_the_client() -> None:
    client = FakeTelegramClient()
    service = NotificationService(
        config=NotificationConfig(enabled=True, bot_token="t", chat_id="c"), client=client
    )

    service.send_signal(SignalType.BUY_CE, make_open_trade())

    assert len(client.messages) == 1
    assert "BUY CE" in client.messages[0]


def test_send_exit_uses_the_correct_message_type() -> None:
    client = FakeTelegramClient()
    service = NotificationService(config=NotificationConfig(enabled=True), client=client)

    service.send_exit(SignalType.TARGET_HIT, make_closed_trade())

    assert service.sent_log[0][0] == NotificationType.TARGET_HIT


def test_send_no_trade() -> None:
    client = FakeTelegramClient()
    service = NotificationService(config=NotificationConfig(enabled=True), client=client)

    service.send_no_trade(make_score(score=40.0), "below threshold")

    assert service.sent_log[0][0] == NotificationType.NO_TRADE


def test_send_daily_summary() -> None:
    client = FakeTelegramClient()
    service = NotificationService(config=NotificationConfig(enabled=True), client=client)

    service.send_daily_summary(make_report())

    assert service.sent_log[0][0] == NotificationType.DAILY_SUMMARY


def test_send_critical_error() -> None:
    client = FakeTelegramClient()
    service = NotificationService(config=NotificationConfig(enabled=True), client=client)

    service.send_critical_error("something broke")

    assert service.sent_log[0][0] == NotificationType.CRITICAL_ERROR
    assert "something broke" in client.messages[0]


def test_send_runtime_started_and_stopped() -> None:
    client = FakeTelegramClient()
    service = NotificationService(config=NotificationConfig(enabled=True), client=client)

    service.send_runtime_started()
    service.send_runtime_stopped()

    assert service.sent_log[0][0] == NotificationType.RUNTIME_STARTED
    assert service.sent_log[1][0] == NotificationType.RUNTIME_STOPPED


def test_a_failed_send_is_logged_but_never_raises() -> None:
    client = FakeTelegramClient(succeeds=False)
    service = NotificationService(config=NotificationConfig(enabled=True), client=client)

    service.send_signal(SignalType.BUY_CE, make_open_trade())  # must not raise


def test_a_client_that_raises_is_caught_and_never_propagates() -> None:
    class ExplodingClient:
        def send_message(self, text: str) -> bool:
            raise RuntimeError("network exploded")

    service = NotificationService(config=NotificationConfig(enabled=True), client=ExplodingClient())

    service.send_signal(SignalType.BUY_CE, make_open_trade())  # must not raise
