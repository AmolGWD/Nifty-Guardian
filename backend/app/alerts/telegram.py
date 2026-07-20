"""
========================================
 NIFTY Guardian Telegram Alerts
========================================

Sends paper trading lifecycle notifications via the Telegram Bot API.
A missing configuration or a failed request never raises - trading
logic must not break because Telegram is unreachable.
"""

import requests

from app.config.settings import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

TELEGRAM_API_URL = "https://api.telegram.org/bot{token}/sendMessage"


def _send(text: str) -> None:
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return

    try:
        requests.post(
            TELEGRAM_API_URL.format(token=TELEGRAM_BOT_TOKEN),
            json={"chat_id": TELEGRAM_CHAT_ID, "text": text},
            timeout=5,
        )
    except requests.RequestException:
        pass


def notify_signal_generated(trade: dict) -> None:
    _send(
        "📡 Signal Generated\n"
        f"Signal: {trade.get('signal')}\n"
        f"Confidence: {trade.get('confidence')}%\n"
        f"Status: {trade.get('status')}"
    )


def notify_trade_opened(trade: dict) -> None:
    _send(
        f"🟢 Paper Trade Opened (#{trade.get('trade_number')})\n"
        f"{trade.get('option_type')} {trade.get('strike')} @ {trade.get('expiry')}\n"
        f"Entry Premium: {trade.get('entry_premium')}\n"
        f"Entry Spot: {trade.get('entry_spot')}\n"
        f"Quantity: {trade.get('quantity')}\n"
        f"Confidence: {trade.get('confidence')}%"
    )


def notify_trade_closed(trade: dict) -> None:
    pnl = trade.get("pnl") or 0
    emoji = "🎯" if pnl > 0 else "❌"
    _send(
        f"{emoji} Paper Trade Closed (#{trade.get('trade_number')})\n"
        f"{trade.get('option_type')} {trade.get('strike')} @ {trade.get('expiry')}\n"
        f"Exit Reason: {trade.get('exit_reason')}\n"
        f"Entry Premium: {trade.get('entry_premium')}\n"
        f"Exit Premium: {trade.get('exit_premium')}\n"
        f"P&L: {pnl}"
    )


def notify_daily_summary(summary: dict) -> None:
    _send(
        "📊 Daily Summary\n"
        f"Total Trades: {summary.get('total_trades')}\n"
        f"Open: {summary.get('open_count')}\n"
        f"Closed: {summary.get('closed_count')}\n"
        f"Wins: {summary.get('wins')}\n"
        f"Losses: {summary.get('losses')}\n"
        f"Win Rate: {summary.get('win_rate')}%\n"
        f"Total P&L: {summary.get('total_pnl')}"
    )


def notify_milestone(closed_count: int, summary: dict) -> None:
    _send(
        f"🏆 Milestone Reached: {closed_count} Trades Closed\n"
        f"Win Rate: {summary.get('win_rate')}%\n"
        f"Total P&L: {summary.get('total_pnl')}"
    )


def notify_system_error(message: str) -> None:
    _send(f"🚨 System Error\n{message}")
