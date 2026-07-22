from datetime import datetime

import pytest

from app.signals.dummy_trade_tracker import DummyTradeTracker
from app.signals.models import DummyTradeStatus, ExitReason, GuardianScore
from app.trading.strategy.models import StrategyDirection, StrategyStrength


def _score() -> GuardianScore:
    return GuardianScore(
        score=90.0, strength=StrategyStrength.STRONG, reward_risk_ratio=2.0, reasons=["r"]
    )


def _open(tracker: DummyTradeTracker, **overrides: object) -> str:
    base: dict[str, object] = dict(
        strategy_name="EMABreakout",
        direction=StrategyDirection.LONG,
        guardian_score=_score(),
        entry_price=100.0,
        stop_loss=95.0,
        target=115.0,
        quantity=10,
        opened_at=datetime(2026, 1, 5, 9, 30),
    )
    base.update(overrides)
    trade = tracker.open_trade(**base)  # type: ignore[arg-type]
    return trade.trade_id


def test_open_trade_starts_in_open_status() -> None:
    tracker = DummyTradeTracker()
    trade_id = _open(tracker)

    trade = tracker.get(trade_id)
    assert trade.status == DummyTradeStatus.OPEN
    assert trade in tracker.open_trades()
    assert trade not in tracker.closed_trades()


def test_close_trade_infers_target_exit_reason() -> None:
    tracker = DummyTradeTracker()
    trade_id = _open(tracker)

    closed = tracker.close_trade(
        trade_id, exit_price=115.0, closed_at=datetime(2026, 1, 5, 11, 0), pnl=150.0
    )

    assert closed.status == DummyTradeStatus.CLOSED
    assert closed.exit_reason == ExitReason.TARGET
    assert closed in tracker.closed_trades()
    assert closed not in tracker.open_trades()


def test_close_trade_infers_stop_loss_exit_reason() -> None:
    tracker = DummyTradeTracker()
    trade_id = _open(tracker)

    closed = tracker.close_trade(
        trade_id, exit_price=95.0, closed_at=datetime(2026, 1, 5, 10, 0), pnl=-50.0
    )

    assert closed.exit_reason == ExitReason.STOP_LOSS


def test_close_trade_infers_end_of_day_when_neither_target_nor_stop_matches() -> None:
    tracker = DummyTradeTracker()
    trade_id = _open(tracker)

    closed = tracker.close_trade(
        trade_id, exit_price=105.0, closed_at=datetime(2026, 1, 5, 15, 30), pnl=50.0
    )

    assert closed.exit_reason == ExitReason.END_OF_DAY


def test_get_missing_trade_raises_key_error() -> None:
    tracker = DummyTradeTracker()
    with pytest.raises(KeyError):
        tracker.get("does-not-exist")


def test_trades_closed_on_filters_by_date() -> None:
    tracker = DummyTradeTracker()
    trade_id = _open(tracker)
    tracker.close_trade(
        trade_id, exit_price=115.0, closed_at=datetime(2026, 1, 5, 11, 0), pnl=150.0
    )

    assert len(tracker.trades_closed_on(datetime(2026, 1, 5, 0, 0))) == 1
    assert len(tracker.trades_closed_on(datetime(2026, 1, 6, 0, 0))) == 0


def test_win_rate_and_net_pnl_helpers() -> None:
    tracker = DummyTradeTracker()
    winner_id = _open(tracker)
    loser_id = _open(tracker)
    winner = tracker.close_trade(
        winner_id, exit_price=115.0, closed_at=datetime(2026, 1, 5, 11, 0), pnl=150.0
    )
    loser = tracker.close_trade(
        loser_id, exit_price=95.0, closed_at=datetime(2026, 1, 5, 12, 0), pnl=-50.0
    )

    trades = [winner, loser]
    assert DummyTradeTracker.win_rate(trades) == 50.0
    assert DummyTradeTracker.net_pnl(trades) == 100.0


def test_win_rate_of_empty_list_is_zero() -> None:
    assert DummyTradeTracker.win_rate([]) == 0.0


def test_build_daily_report_summarizes_the_day() -> None:
    tracker = DummyTradeTracker()
    winner_id = _open(tracker)
    loser_id = _open(tracker)
    tracker.close_trade(
        winner_id, exit_price=115.0, closed_at=datetime(2026, 1, 5, 11, 0), pnl=150.0
    )
    tracker.close_trade(
        loser_id, exit_price=95.0, closed_at=datetime(2026, 1, 5, 12, 0), pnl=-50.0
    )

    report = tracker.build_daily_report(datetime(2026, 1, 5))

    assert report.report_date == "2026-01-05"
    assert report.total_signals == 2
    assert report.winning_trades == 1
    assert report.losing_trades == 1
    assert report.win_rate == 50.0
    assert report.net_points == 100.0
    assert report.best_trade is not None and report.best_trade.pnl == 150.0
    assert report.worst_trade is not None and report.worst_trade.pnl == -50.0


def test_build_daily_report_with_no_trades_is_all_zeros() -> None:
    tracker = DummyTradeTracker()
    report = tracker.build_daily_report(datetime(2026, 1, 5))

    assert report.total_signals == 0
    assert report.win_rate == 0.0
    assert report.best_trade is None
    assert report.worst_trade is None
