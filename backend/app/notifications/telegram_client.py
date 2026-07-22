"""
The one seam to the real Telegram Bot API - `TelegramClientInterface`
is a `Protocol`, mirroring `app.brokers.interface.KiteConnectClient`'s
own seam pattern, so `NotificationService`/tests never need a real
bot token or network access. `HttpTelegramClient` uses only the
standard library (`urllib.request`) - no new runtime dependency for
a single HTTP POST.
"""

import json
import logging
import urllib.error
import urllib.request
from typing import Protocol

logger = logging.getLogger(__name__)

_TELEGRAM_API_BASE = "https://api.telegram.org"


class TelegramClientInterface(Protocol):
    def send_message(self, text: str) -> bool: ...


class HttpTelegramClient:
    def __init__(self, *, bot_token: str, chat_id: str, timeout_seconds: float = 10.0) -> None:
        self._bot_token = bot_token
        self._chat_id = chat_id
        self._timeout_seconds = timeout_seconds

    def send_message(self, text: str) -> bool:
        url = f"{_TELEGRAM_API_BASE}/bot{self._bot_token}/sendMessage"
        payload = json.dumps({"chat_id": self._chat_id, "text": text}).encode("utf-8")
        request = urllib.request.Request(
            url, data=payload, headers={"Content-Type": "application/json"}, method="POST"
        )
        try:
            with urllib.request.urlopen(request, timeout=self._timeout_seconds) as response:
                status: int = response.status
                return 200 <= status < 300
        except urllib.error.URLError:
            logger.exception("HttpTelegramClient: failed to send Telegram message")
            return False
