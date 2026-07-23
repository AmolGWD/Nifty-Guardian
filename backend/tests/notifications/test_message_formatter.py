from app.notifications.message_formatter import (
    format_critical_error_message,
    format_daily_summary_message,
    format_exit_message,
    format_no_trade_message,
    format_runtime_event_message,
    format_signal_message,
)
from app.signals.models import SignalType
from tests.notifications.helpers import make_closed_trade, make_open_trade, make_report, make_score


def test_format_signal_message_contains_every_required_field() -> None:
    trade = make_open_trade()
    message = format_signal_message(SignalType.BUY_CE, trade)

    assert "🟢 BUY CE" in message
    assert "Confidence: 90%" in message
    assert "Entry: 100.00" in message
    assert "Stop Loss: 95.00" in message
    assert "Target: 115.00" in message
    assert "Risk Reward: 2.00" in message
    assert "✓ EMA alignment: price above EMA" in message
    assert "Signal Time: 2026-01-05 09:30:00" in message


def test_format_signal_message_buy_pe_label() -> None:
    trade = make_open_trade(direction="Short")
    message = format_signal_message(SignalType.BUY_PE, trade)
    assert "BUY PE" in message


def test_format_exit_message_target_hit() -> None:
    trade = make_closed_trade()
    message = format_exit_message(SignalType.TARGET_HIT, trade)

    assert "TARGET HIT" in message
    assert "Entry: 100.00" in message
    assert "Exit: 115.00" in message
    assert "PnL: 750.00" in message
    assert "R Multiple:" in message


def test_format_exit_message_stoploss_hit() -> None:
    trade = make_closed_trade(exit_price=95.0, pnl=-250.0)
    message = format_exit_message(SignalType.STOPLOSS_HIT, trade)
    assert "STOPLOSS HIT" in message


def test_format_no_trade_message() -> None:
    message = format_no_trade_message(make_score(score=40.0), "below threshold")
    assert "NO TRADE" in message
    assert "Guardian Score: 40.0" in message
    assert "below threshold" in message


def test_format_daily_summary_message() -> None:
    message = format_daily_summary_message(make_report())
    assert "📊 Guardian Daily Summary" in message
    assert "Trading Date: 2026-01-05" in message
    assert "BUY CE: 1" in message
    assert "BUY PE: 1" in message
    assert "Win Rate: 50.0%" in message
    assert "Total PnL: 100.00" in message
    assert "Average PnL: 50.00" in message
    assert "Highest Guardian Score: 90.0" in message
    assert "Average Hold Time: 1h 30m" in message
    assert "Market Bias: Long" in message
    assert "Guardian Status: Active" in message


def test_format_daily_summary_message_with_no_trades() -> None:
    report = make_report(
        total_signals=0, buy_ce_count=0, buy_pe_count=0, winning_trades=0, losing_trades=0,
        win_rate=0.0, net_points=0.0, average_pnl=0.0, average_reward_risk_ratio=0.0,
        best_trade=None, worst_trade=None, highest_guardian_score=0.0,
        average_hold_time_seconds=0.0,
    )
    message = format_daily_summary_message(report)
    assert "Best Trade: -" in message
    assert "Worst Trade: -" in message
    assert "Average Hold Time: 0m" in message


def test_format_critical_error_message() -> None:
    message = format_critical_error_message("broker connection lost")
    assert "CRITICAL ERROR" in message
    assert "broker connection lost" in message


def test_format_runtime_event_message() -> None:
    assert "RUNTIME STARTED" in format_runtime_event_message(started=True)
    assert "RUNTIME STOPPED" in format_runtime_event_message(started=False)
