#!/usr/bin/env python3
"""
Standalone demonstration of the Signal Engine, Telegram Alerts, and
Dummy Trade Tracking - the operational layer turning the completed
platform into "leave it running, get alerted."

Wires `app.signals.start_signal_engine()` (which itself wires the
frozen `app.live.start_live_runtime()` + a new `SignalService`) over a
`ReplayMarketFeed` of synthetic uptrend candles and a `PaperBroker`,
with `NotificationService` pointed at a fake Telegram client (no real
bot token, no real network access). Demonstrates: receiving candles,
generating a high-confidence signal, a Guardian Score with reasons,
creating a dummy trade, a Telegram alert, a target-hit exit, and an
end-of-day report exported to JSON.

No real order is ever placed - the broker is always `PaperBroker`.

Run from the backend directory (see docs/INSTALLATION_GUIDE.md for why):

    cd backend && python3 ../scripts/demo_signal_engine.py
"""

from __future__ import annotations

import sys
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

_BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

from app.live.live_market_feed import ReplayMarketFeed, run_feed_in_background  # noqa: E402
from app.live.models import LiveConfig  # noqa: E402
from app.market_data.schemas import Candle  # noqa: E402
from app.notifications.models import NotificationConfig  # noqa: E402
from app.notifications.notification_service import NotificationService  # noqa: E402
from app.paper_trading.paper_broker import PaperBroker  # noqa: E402
from app.signals.models import SignalConfig  # noqa: E402
from app.signals.signal_runtime import start_signal_engine  # noqa: E402


def _print_header(title: str) -> None:
    banner = "=" * 70
    print(f"\n{banner}\n{title}\n{banner}")


def _build_candles(n: int, *, per_day: int = 25) -> list[Candle]:
    """
    Synthetic weekday-only 15-minute candles in a mild uptrend, rolling
    over to the next trading day's 09:15 after `per_day` candles - the
    same generator `tests/runtime/helpers.py` and Phase 24's own demo
    script already use, so the Strategy Engine sees multiple real
    trading-hours windows rather than one candle stream that drifts
    past market close and never returns.
    """
    start = datetime(2026, 1, 5, 9, 15)
    candles: list[Candle] = []
    timestamp = start
    close = 100.0
    count_today = 0

    while len(candles) < n:
        if timestamp.weekday() >= 5:
            timestamp += timedelta(days=1)
            continue

        open_price = close
        close = close + 2.0
        high = max(open_price, close) + 1.0
        low = min(open_price, close) - 1.0
        candles.append(
            Candle(
                timestamp=timestamp, open=open_price, high=high, low=low, close=close,
                volume=10_000,
            )
        )
        timestamp += timedelta(minutes=15)
        count_today += 1
        if count_today >= per_day:
            timestamp += timedelta(hours=16)
            count_today = 0

    return candles


class FakeTelegramClient:
    """A fake Telegram client - captures every message, no real network access."""

    def __init__(self) -> None:
        self.messages: list[str] = []

    def send_message(self, text: str) -> bool:
        self.messages.append(text)
        return True


def main() -> None:
    candles = _build_candles(60)
    feed = ReplayMarketFeed(candles)
    broker = PaperBroker()
    fake_telegram = FakeTelegramClient()

    reports_directory = Path(tempfile.mkdtemp()) / "reports"

    _print_header("1. WIRE THE SIGNAL ENGINE (Signal Service + Notification Service + Runtime)")
    notification_service = NotificationService(
        config=NotificationConfig(enabled=True, bot_token="demo", chat_id="demo"),
        client=fake_telegram,
    )
    signal_config = SignalConfig(confidence_threshold=0.0, cooldown_minutes=0.0)
    ctx = start_signal_engine(
        market_feed=feed,
        broker=broker,
        expected_candle_count=len(candles),
        live_config=LiveConfig(live_mode=False),
        signal_config=signal_config,
        notification_service=notification_service,
        reports_directory=reports_directory,
    )
    print("  LiveConfig.live_mode = False (paper-safe default - never a real order)")
    print("  TELEGRAM_ENABLED = true, pointed at a fake client (no real network access)")

    _print_header("2. CONNECT AND START TRADING")
    ctx.live_context.live_session.connect()
    ctx.live_context.live_session.start_trading()

    _print_header("3. RECEIVE CANDLES AND DETECT A SIGNAL")
    feed.connect()
    thread = run_feed_in_background(feed)
    ctx.live_context.runtime_engine.run()
    thread.join(timeout=5.0)
    print(f"  Candles processed: {ctx.live_context.runtime_engine.processed_count}")
    print(f"  Market bias: {ctx.signal_service.state.market_bias.value}")

    _print_header("4. DUMMY TRADE HISTORY")
    for trade in ctx.signal_service.tracker.all_trades():
        print(
            f"  #{trade.trade_id[:8]} {trade.status.value}: entry={trade.entry_price:.2f} "
            f"sl={trade.stop_loss:.2f} target={trade.target:.2f} "
            f"exit={trade.exit_price} pnl={trade.pnl} reason={trade.exit_reason}"
        )

    _print_header("5. TELEGRAM MESSAGES SENT (fake client - no real network access)")
    for message in fake_telegram.messages:
        print(f"\n{message}\n{'-' * 40}")

    _print_header("6. END-OF-DAY REPORT (on-demand export)")
    # Report for the day the trades actually closed on, not the last candle's
    # date - candle generation may have already rolled over to the next
    # trading day by the time the replay finishes.
    closed = ctx.signal_service.tracker.closed_trades()
    report_as_of = closed[-1].closed_at if closed else candles[-1].timestamp
    export_path = ctx.signal_service.export_report_now(report_as_of)
    print(f"  Exported to: {export_path}")
    print(f"  Contents:\n{export_path.read_text()}")

    _print_header("Demo complete - no real broker connectivity, no real order ever placed")


if __name__ == "__main__":
    main()
