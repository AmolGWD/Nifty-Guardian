"""
Renders the exact Telegram message format the CTO brief specifies.
Every field is sourced from an already-computed `DummyTrade`/
`GuardianScore`/`DailyPerformanceReport` (app.signals, this phase) -
nothing here computes anything new.

"Reasons" lists exactly what `GuardianScore.reasons` carries - the
per-check strings the (frozen) Strategy Engine itself already produces
(e.g. "EMA alignment: price above EMA", "RSI confirmation: RSI 62.34
above 55"). The brief's message template also names OI and Pivot as
reason categories; the currently-registered EMABreakout strategy
doesn't evaluate either, so this formatter never fabricates a line for
them - only real, strategy-produced reasons are ever printed.
"""

from app.signals.models import DailyPerformanceReport, DummyTrade, GuardianScore, SignalType

_EMOJI_BY_SIGNAL_TYPE: dict[SignalType, str] = {
    SignalType.BUY_CE: "🟢",
    SignalType.BUY_PE: "🔴",
    SignalType.TARGET_HIT: "🎯",
    SignalType.STOPLOSS_HIT: "🛑",
    SignalType.NO_TRADE: "⚪",
}


def _header(emoji: str, label: str) -> str:
    return f"{emoji} NIFTY GUARDIAN\n{label}"


def format_signal_message(signal_type: SignalType, trade: DummyTrade) -> str:
    emoji = _EMOJI_BY_SIGNAL_TYPE[signal_type]
    label = "BUY CE" if signal_type == SignalType.BUY_CE else "BUY PE"
    reasons = "\n".join(f"- {reason}" for reason in trade.guardian_score.reasons)
    return (
        f"{_header(emoji, label)}\n\n"
        f"Time: {trade.opened_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"Signal: {label}\n"
        f"Confidence: {trade.guardian_score.strength.value}\n"
        f"Guardian Score: {trade.guardian_score.score:.1f}\n\n"
        f"Entry: {trade.entry_price:.2f}\n"
        f"SL: {trade.stop_loss:.2f}\n"
        f"Target: {trade.target:.2f}\n"
        f"RR: {trade.guardian_score.reward_risk_ratio:.2f}\n\n"
        f"Reasons:\n{reasons}\n\n"
        f"Dummy Trade #{trade.trade_id[:8]}"
    )


def format_exit_message(signal_type: SignalType, trade: DummyTrade) -> str:
    emoji = _EMOJI_BY_SIGNAL_TYPE[signal_type]
    label = "TARGET HIT" if signal_type == SignalType.TARGET_HIT else "STOPLOSS HIT"
    return (
        f"{_header(emoji, label)}\n\n"
        f"Time: {(trade.closed_at or trade.opened_at).strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"Entry: {trade.entry_price:.2f}\n"
        f"Exit: {(trade.exit_price or 0.0):.2f}\n"
        f"PnL: {(trade.pnl or 0.0):.2f}\n"
        f"R Multiple: {(trade.r_multiple or 0.0):.2f}\n\n"
        f"Dummy Trade #{trade.trade_id[:8]}"
    )


def format_no_trade_message(guardian_score: GuardianScore, reason: str) -> str:
    return (
        f"{_header('⚪', 'NO TRADE')}\n\n"
        f"Confidence: {guardian_score.strength.value}\n"
        f"Guardian Score: {guardian_score.score:.1f}\n"
        f"Reason: {reason}"
    )


def format_daily_summary_message(report: DailyPerformanceReport) -> str:
    best = f"{report.best_trade.pnl:.2f}" if report.best_trade and report.best_trade.pnl else "-"
    worst = (
        f"{report.worst_trade.pnl:.2f}" if report.worst_trade and report.worst_trade.pnl else "-"
    )
    return (
        f"{_header('📊', 'DAILY SUMMARY')}\n\n"
        f"Date: {report.report_date}\n"
        f"Total Signals: {report.total_signals}\n"
        f"Winning Trades: {report.winning_trades}\n"
        f"Losing Trades: {report.losing_trades}\n"
        f"Win Rate: {report.win_rate:.1f}%\n"
        f"Net Points: {report.net_points:.2f}\n"
        f"Average RR: {report.average_reward_risk_ratio:.2f}\n"
        f"Best Trade: {best}\n"
        f"Worst Trade: {worst}"
    )


def format_critical_error_message(message: str) -> str:
    return f"{_header('⚠️', 'CRITICAL ERROR')}\n\n{message}"


def format_runtime_event_message(*, started: bool) -> str:
    label = "RUNTIME STARTED" if started else "RUNTIME STOPPED"
    emoji = "🟢" if started else "🔴"
    return f"{_header(emoji, label)}"
