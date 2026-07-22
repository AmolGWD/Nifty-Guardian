import urllib.error
from unittest.mock import MagicMock, patch

from app.notifications.telegram_client import HttpTelegramClient


def test_send_message_returns_true_on_a_2xx_response() -> None:
    client = HttpTelegramClient(bot_token="tok", chat_id="123")
    fake_response = MagicMock()
    fake_response.status = 200
    fake_response.__enter__.return_value = fake_response

    with patch("urllib.request.urlopen", return_value=fake_response) as mock_urlopen:
        assert client.send_message("hello") is True

    request = mock_urlopen.call_args[0][0]
    assert request.full_url == "https://api.telegram.org/bottok/sendMessage"
    assert request.get_method() == "POST"


def test_send_message_returns_false_on_a_url_error() -> None:
    client = HttpTelegramClient(bot_token="tok", chat_id="123")

    with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("boom")):
        assert client.send_message("hello") is False


def test_send_message_returns_false_on_a_non_2xx_response() -> None:
    client = HttpTelegramClient(bot_token="tok", chat_id="123")
    fake_response = MagicMock()
    fake_response.status = 500
    fake_response.__enter__.return_value = fake_response

    with patch("urllib.request.urlopen", return_value=fake_response):
        assert client.send_message("hello") is False
