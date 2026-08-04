"""
`SignalEngineRuntimeService`: the one live Signal Engine session this
API process drives - mirrors `app.api.dashboard.dashboard_service.
DashboardRuntimeService`'s own pattern (Phase 22) exactly, but wires
`app.signals.signal_runtime.start_signal_engine()` instead of
`app.runtime.startup.start_runtime()`, since this service needs a
`SignalService`/`NotificationService` attached, which the dashboard's
own wiring doesn't provide. Entirely new, additive package -
`app.api.dashboard` itself is completely untouched.

Reuses the exact same sample dataset `dashboard_service.py` already
replays (`app/market_data/sample_data/nifty_sample_candles.csv`,
shipped inside the `app` package so it survives a container image that
only ever copies `app/`; see that module's own path-resolution
comment), materialized through the frozen `HistoricalReplaySource` (so
no new CSV-parsing code exists anywhere) and re-wrapped in a
`ReplayMarketFeed` (Phase 24) - `HistoricalReplaySource` and
`ReplayMarketFeed` are different Protocols for a good reason (pull vs.
push), but nothing stops materializing one into the list the other
wants.

Broker is always `PaperBroker` - this service creates dummy trades
only, exactly as `app.signals.signal_runtime`'s own module docstring
requires. `NotificationConfig`/`SignalConfig` are constructed with no
arguments, so they read `TELEGRAM_*`/`SIGNAL_*` from the real
environment at request time - an operator sets those in `.env` (or
`config/*.env`), this service picks them up automatically.
"""

import os
import threading
from datetime import datetime, timedelta
from pathlib import Path

from app.api.signals.signals_models import (
    DailyReportResponse,
    DummyTradeResponse,
    EngineStatusResponse,
    ExportReportResponse,
    GuardianScoreResponse,
    PerformanceResponse,
    SignalStateResponse,
)
from app.live.live_market_feed import ReplayMarketFeed, run_feed_in_background
from app.live.models import LiveConfig
from app.notifications.models import NotificationConfig
from app.notifications.notification_service import NotificationService
from app.notifications.telegram_client import HttpTelegramClient
from app.paper_trading.paper_broker import PaperBroker
from app.runtime.market_data_source import HistoricalReplaySource
from app.signals.dummy_trade_tracker import DummyTradeTracker
from app.signals.models import DummyTrade, GuardianScore, SignalConfig
from app.signals.signal_runtime import SignalEngineContext, start_signal_engine
from app.signals.signal_service import SignalService
from app.trading.strategy.models import StrategyDirection

# Resolved relative to the `app` package root (parents[2] from this file:
# signals -> api -> app), not the repo root - so it still resolves
# correctly inside a container image that only ever copies `app/` (see
# `backend/Dockerfile`), regardless of the repo's own directory layout.
# Same deployment copy `dashboard_service.py` uses - see that module's
# own `_SAMPLE_DATASET_PATH` docstring comment.
_DEFAULT_SAMPLE_DATASET_PATH = (
    Path(__file__).resolve().parents[2]
    / "market_data"
    / "sample_data"
    / "nifty_sample_candles.csv"
)
# Override for demonstrating/verifying the SHORT ("BUY PE") path against a
# genuinely bearish candle series - e.g. scripts/sample_data/
# nifty_sample_bearish_candles.csv. Unset (the default) replays the same
# bullish sample dataset this service has always used - zero behavior change.
_SAMPLE_DATASET_PATH = Path(
    os.environ.get("SIGNAL_SAMPLE_DATASET_PATH", str(_DEFAULT_SAMPLE_DATASET_PATH))
)


class SignalEngineConflictError(Exception):
    """Raised when a requested action conflicts with the current session state."""


def _guardian_score_response(score: GuardianScore) -> GuardianScoreResponse:
    return GuardianScoreResponse(
        score=score.score,
        strength=score.strength,
        reward_risk_ratio=score.reward_risk_ratio,
        reasons=score.reasons,
    )


def _trade_response(trade: DummyTrade) -> DummyTradeResponse:
    return DummyTradeResponse(
        trade_id=trade.trade_id,
        strategy_name=trade.strategy_name,
        direction=trade.direction,
        guardian_score=_guardian_score_response(trade.guardian_score),
        entry_price=trade.entry_price,
        stop_loss=trade.stop_loss,
        target=trade.target,
        quantity=trade.quantity,
        opened_at=trade.opened_at,
        status=trade.status,
        exit_price=trade.exit_price,
        closed_at=trade.closed_at,
        pnl=trade.pnl,
        r_multiple=trade.r_multiple,
        duration_seconds=trade.duration_seconds,
        exit_reason=trade.exit_reason,
    )


class SignalEngineRuntimeService:
    def __init__(self) -> None:
        self._context: SignalEngineContext | None = None
        self._notification_service: NotificationService | None = None
        self._lock = threading.Lock()

    def start(self) -> EngineStatusResponse:
        with self._lock:
            if self._context is not None:
                raise SignalEngineConflictError("signal engine session already running")

            candles = list(HistoricalReplaySource(str(_SAMPLE_DATASET_PATH)))
            feed = ReplayMarketFeed(candles)
            broker = PaperBroker()

            notification_config = NotificationConfig()
            client = HttpTelegramClient(
                bot_token=notification_config.bot_token, chat_id=notification_config.chat_id
            )
            notification_service = NotificationService(config=notification_config, client=client)

            context = start_signal_engine(
                market_feed=feed,
                broker=broker,
                expected_candle_count=len(candles),
                live_config=LiveConfig(live_mode=False),
                signal_config=SignalConfig(),
                notification_service=notification_service,
            )

            context.live_context.live_session.connect()
            context.live_context.live_session.start_trading()
            notification_service.send_runtime_started()

            feed.connect()
            run_feed_in_background(feed)
            threading.Thread(target=context.live_context.runtime_engine.run, daemon=True).start()

            self._context = context
            self._notification_service = notification_service
            return self._status()

    def stop(self) -> EngineStatusResponse:
        with self._lock:
            context = self._require_context()
            context.live_context.live_session.stop()
            if self._notification_service is not None:
                self._notification_service.send_runtime_stopped()
            self._context = None
            self._notification_service = None
            return EngineStatusResponse(running=False, live_session_state=None)

    def status(self) -> EngineStatusResponse:
        with self._lock:
            return self._status()

    def _status(self) -> EngineStatusResponse:
        if self._context is None:
            return EngineStatusResponse(running=False, live_session_state=None)
        return EngineStatusResponse(
            running=True, live_session_state=self._context.live_context.live_session.state.value
        )

    def state(self) -> SignalStateResponse:
        signal_service = self._signal_service_or_none()
        if signal_service is None:
            return SignalStateResponse(
                market_status=None,
                market_bias=StrategyDirection.NONE,
                latest_signal_type=None,
                latest_guardian_score=None,
                latest_explanation=None,
                latest_signal_at=None,
                latest_entry_price=None,
                latest_stop_loss=None,
                latest_target=None,
                signals_sent_today=0,
                telegram_status=None,
            )

        state = signal_service.state
        return SignalStateResponse(
            market_status=state.market_status,
            market_bias=state.market_bias,
            latest_signal_type=state.latest_signal_type,
            latest_guardian_score=(
                _guardian_score_response(state.latest_guardian_score)
                if state.latest_guardian_score is not None
                else None
            ),
            latest_explanation=state.latest_explanation,
            latest_signal_at=state.latest_signal_at,
            latest_entry_price=state.latest_entry_price,
            latest_stop_loss=state.latest_stop_loss,
            latest_target=state.latest_target,
            signals_sent_today=signal_service.signals_sent_today,
            telegram_status=(
                self._notification_service.last_status
                if self._notification_service is not None
                else None
            ),
        )

    def performance(self) -> PerformanceResponse:
        tracker = self._tracker_or_none()
        if tracker is None:
            return PerformanceResponse(
                open_trades=[], closed_trades=[], win_rate=0.0, today_pnl=0.0,
                weekly_pnl=0.0, monthly_pnl=0.0,
            )

        now = datetime.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = today_start - timedelta(days=now.weekday())
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        closed = tracker.closed_trades()
        today_trades = tracker.trades_closed_on(now)
        weekly_trades = tracker.trades_closed_between(week_start, now)
        monthly_trades = tracker.trades_closed_between(month_start, now)

        return PerformanceResponse(
            open_trades=[_trade_response(t) for t in tracker.open_trades()],
            closed_trades=[_trade_response(t) for t in closed],
            win_rate=DummyTradeTracker.win_rate(closed),
            today_pnl=DummyTradeTracker.net_pnl(today_trades),
            weekly_pnl=DummyTradeTracker.net_pnl(weekly_trades),
            monthly_pnl=DummyTradeTracker.net_pnl(monthly_trades),
        )

    def trades(self) -> list[DummyTradeResponse]:
        tracker = self._tracker_or_none()
        if tracker is None:
            return []
        return [_trade_response(t) for t in tracker.all_trades()]

    def report_today(self) -> DailyReportResponse:
        tracker = self._tracker_or_none()
        if tracker is None:
            report_date = datetime.now().date().isoformat()
            return DailyReportResponse(
                report_date=report_date, total_signals=0, buy_ce_count=0, buy_pe_count=0,
                winning_trades=0, losing_trades=0, win_rate=0.0, net_points=0.0,
                average_pnl=0.0, average_reward_risk_ratio=0.0, best_trade=None, worst_trade=None,
                highest_guardian_score=0.0, average_hold_time_seconds=0.0,
                market_bias=StrategyDirection.NONE, guardian_status="Inactive",
            )

        signal_service = self._signal_service_or_none()
        market_bias = signal_service.state.market_bias if signal_service is not None else (
            StrategyDirection.NONE
        )
        report = tracker.build_daily_report(
            datetime.now(), market_bias=market_bias, guardian_status="Active"
        )
        return DailyReportResponse(
            report_date=report.report_date,
            total_signals=report.total_signals,
            buy_ce_count=report.buy_ce_count,
            buy_pe_count=report.buy_pe_count,
            winning_trades=report.winning_trades,
            losing_trades=report.losing_trades,
            win_rate=report.win_rate,
            net_points=report.net_points,
            average_pnl=report.average_pnl,
            average_reward_risk_ratio=report.average_reward_risk_ratio,
            best_trade=_trade_response(report.best_trade) if report.best_trade else None,
            worst_trade=_trade_response(report.worst_trade) if report.worst_trade else None,
            highest_guardian_score=report.highest_guardian_score,
            average_hold_time_seconds=report.average_hold_time_seconds,
            market_bias=report.market_bias,
            guardian_status=report.guardian_status,
        )

    def export_report_now(self) -> ExportReportResponse:
        signal_service = self._signal_service_or_none()
        if signal_service is None:
            raise SignalEngineConflictError("no signal engine session is running")
        path = signal_service.export_report_now()
        return ExportReportResponse(path=str(path))

    def _signal_service_or_none(self) -> SignalService | None:
        return self._context.signal_service if self._context is not None else None

    def _tracker_or_none(self) -> DummyTradeTracker | None:
        signal_service = self._signal_service_or_none()
        return signal_service.tracker if signal_service is not None else None

    def _require_context(self) -> SignalEngineContext:
        if self._context is None:
            raise SignalEngineConflictError("no signal engine session is running")
        return self._context


signal_engine_runtime_service = SignalEngineRuntimeService()
