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
    """
    "Confidence: XX%" reuses the existing Guardian Score (0-100, already
    computed by `app.signals.confidence_engine` - nothing recalculated
    here) formatted as a percentage; `StrategyStrength` (Strong/
    Moderate/Weak) has no percentage representation, so the numeric
    Guardian Score is what maps onto this template's "XX%" field.
    Reasons are exactly `GuardianScore.reasons` (unchanged) with a
    checkmark prefix - the same five checks, in the same order
    (EMA/RSI/VWAP/SuperTrend/Trend), the frozen Strategy Engine already
    produces.
    """
    emoji = _EMOJI_BY_SIGNAL_TYPE[signal_type]
    label = "BUY CE" if signal_type == SignalType.BUY_CE else "BUY PE"
    reasons = "\n".join(f"✓ {reason}" for reason in trade.guardian_score.reasons)
    return (
        f"{emoji} {label}\n\n"
        f"Confidence: {trade.guardian_score.score:.0f}%\n\n"
        f"Entry: {trade.entry_price:.2f}\n"
        f"Stop Loss: {trade.stop_loss:.2f}\n"
        f"Target: {trade.target:.2f}\n"
        f"Risk Reward: {trade.guardian_score.reward_risk_ratio:.2f}\n\n"
        f"Reasons\n\n{reasons}\n\n"
        f"Signal Time: {trade.opened_at.strftime('%Y-%m-%d %H:%M:%S')}"
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


def _format_hold_time(seconds: float) -> str:
    minutes, _ = divmod(round(seconds), 60)
    hours, minutes = divmod(minutes, 60)
    return f"{hours}h {minutes}m" if hours else f"{minutes}m"


def format_daily_summary_message(report: DailyPerformanceReport) -> str:
    """
    Every field is read straight off `DailyPerformanceReport`
    (`app.signals.dummy_trade_tracker.build_daily_report()`) - nothing
    here recomputes PnL, win rate, or trade counts a second time.
    """
    best = f"{report.best_trade.pnl:.2f}" if report.best_trade and report.best_trade.pnl else "-"
    worst = (
        f"{report.worst_trade.pnl:.2f}" if report.worst_trade and report.worst_trade.pnl else "-"
    )
    return (
        "📊 Guardian Daily Summary\n\n"
        f"Trading Date: {report.report_date}\n"
        f"Total Signals: {report.total_signals}\n"
        f"BUY CE: {report.buy_ce_count}\n"
        f"BUY PE: {report.buy_pe_count}\n"
        f"Winning Trades: {report.winning_trades}\n"
        f"Losing Trades: {report.losing_trades}\n"
        f"Win Rate: {report.win_rate:.1f}%\n"
        f"Total PnL: {report.net_points:.2f}\n"
        f"Average PnL: {report.average_pnl:.2f}\n"
        f"Best Trade: {best}\n"
        f"Worst Trade: {worst}\n"
        f"Highest Guardian Score: {report.highest_guardian_score:.1f}\n"
        f"Average Hold Time: {_format_hold_time(report.average_hold_time_seconds)}\n"
        f"Market Bias: {report.market_bias.value}\n"
        f"Guardian Status: {report.guardian_status}"
    )


def format_critical_error_message(message: str) -> str:
    return f"{_header('⚠️', 'CRITICAL ERROR')}\n\n{message}"


def format_runtime_event_message(*, started: bool) -> str:
    label = "RUNTIME STARTED" if started else "RUNTIME STOPPED"
    emoji = "🟢" if started else "🔴"
    return f"{_header(emoji, label)}"
