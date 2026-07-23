"""
SignalService: the orchestrator described in the CTO brief - receives
completed trading decisions (subscribing to the frozen `EventBus`
exactly the way `ExecutionJournal`/`PerformanceMonitor` already do),
filters duplicates, applies the confidence threshold, generates a
human-readable explanation, updates queryable dashboard state, sends a
Telegram message, creates a dummy trade, and records history. No
business logic duplication - every trading decision was already made
by the frozen Strategy/Risk/Decision Engines before this class ever
sees it; this class only decides whether/how to *report* it.

Honest limitation, not a defect: the frozen `app.runtime.event_processor`
only ever submits a real (paper) order for `StrategyDirection.LONG`
recommendations (see its own `_evaluate_entry()` - it requires
`recommendation.direction == StrategyDirection.LONG` before calling
`order_manager.submit()`). "BUY PE" is fully supported by every type
here (`SignalType.BUY_PE`, `NotificationType.BUY_PE`) and will work the
day a future, explicitly-authorized phase adds SHORT order submission
to the runtime - but under today's frozen runtime, only "BUY CE"-style
(LONG) signals can ever actually fire.

Correlating a dummy trade's close (`PositionUpdatedEvent`) back to the
`OrderFilledEvent` that opened it relies on `app.paper_trading`'s own
documented invariant that at most one position is open at a time
(`event_processor.py`: "if self._open_position_id is None:
self._evaluate_entry(...)") - so a per-strategy pending slot is always
unambiguous. `Position` never records the exit price directly (only
realized P&L) - `_infer_exit_price()` derives it from the same
`_signed_pnl()` formula `PositionManager` (frozen) itself uses,
documented here rather than silently assumed.

Trading-hours filtering and dummy-trade timestamps use the *candle's*
own timestamp (from `MarketDataReceivedEvent`), not `Order.updated_at`/
`Position.closed_at` - both of the latter are wall-clock (`datetime.
now()`) inside the frozen `PaperBroker`/`PositionManager`, which only
matches the market's actual clock when driven by a genuinely live feed.
During a replay (a demo, a test, catching up on missed candles),
wall-clock and candle-time diverge completely - tracking the candle's
own timestamp keeps trading-hours enforcement and trade duration
meaningful in both cases, with zero behavior change for a real live
feed (where candle time and wall-clock time are the same moment).
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Protocol

from app.paper_trading.event_bus import EventBus
from app.paper_trading.events import (
    MarketDataReceivedEvent,
    OrderFilledEvent,
    PositionUpdatedEvent,
    SignalGeneratedEvent,
)
from app.paper_trading.models import PositionStatus
from app.signals.confidence_engine import compute_guardian_score
from app.signals.dummy_trade_tracker import DummyTradeTracker
from app.signals.models import (
    DailyPerformanceReport,
    DummyTrade,
    ExitReason,
    GuardianScore,
    SignalConfig,
    SignalType,
)
from app.signals.report_exporter import DEFAULT_REPORTS_DIRECTORY, export_daily_report_json
from app.signals.signal_filter import SessionPhase, SignalFilter, classify_session
from app.trading.strategy.models import StrategyDirection, StrategyEvaluation

logger = logging.getLogger(__name__)

_EXIT_REASON_TO_NOTIFICATION_SIGNAL_TYPE: dict[ExitReason, SignalType] = {
    ExitReason.TARGET: SignalType.TARGET_HIT,
    ExitReason.STOP_LOSS: SignalType.STOPLOSS_HIT,
}


class NotificationSink(Protocol):
    """The one seam `SignalService` needs into `app.notifications` - kept local to avoid a
    package-level dependency in either direction; `NotificationService` satisfies this
    structurally, the same Protocol-seam pattern `BrokerInterface`/`MarketDataClient` use."""

    def send_signal(self, signal_type: SignalType, trade: DummyTrade) -> None: ...

    def send_exit(self, signal_type: SignalType, trade: DummyTrade) -> None: ...

    def send_no_trade(self, guardian_score: GuardianScore, reason: str) -> None: ...

    def send_daily_summary(self, report: DailyPerformanceReport) -> None: ...


class CurrentSignalState:
    """Read-only, queryable snapshot the dashboard API layer polls - never mutated externally."""

    def __init__(self) -> None:
        self.market_status: SessionPhase | None = None
        self.market_bias: StrategyDirection = StrategyDirection.NONE
        self.latest_signal_type: SignalType | None = None
        self.latest_guardian_score: GuardianScore | None = None
        self.latest_explanation: str | None = None
        self.latest_signal_at: datetime | None = None
        self.latest_entry_price: float | None = None
        self.latest_stop_loss: float | None = None
        self.latest_target: float | None = None


def _infer_exit_price(
    *, direction: StrategyDirection, entry_price: float, realized_pnl: float, initial_quantity: int
) -> float:
    if initial_quantity == 0:
        return entry_price
    per_unit = realized_pnl / initial_quantity
    if direction == StrategyDirection.SHORT:
        return entry_price - per_unit
    return entry_price + per_unit


class SignalService:
    def __init__(
        self,
        *,
        config: SignalConfig,
        notification_service: NotificationSink,
        tracker: DummyTradeTracker | None = None,
        signal_filter: SignalFilter | None = None,
        reports_directory: Path | None = None,
    ) -> None:
        self._config = config
        self._notifications = notification_service
        self._tracker = tracker or DummyTradeTracker()
        self._filter = signal_filter or SignalFilter(config=config)
        self._state = CurrentSignalState()
        self._reports_directory = reports_directory or DEFAULT_REPORTS_DIRECTORY
        self._last_exported_report_path: Path | None = None

        self._last_evaluation_by_strategy: dict[str, StrategyEvaluation] = {}
        self._pending_trade_by_strategy: dict[str, str] = {}
        self._position_id_to_trade_id: dict[str, str] = {}
        self._last_no_trade_notified_at: datetime | None = None
        self._report_generated_for_date: str | None = None
        self._latest_candle_at: datetime | None = None
        self._market_open_seen_on_date: str | None = None

    def subscribe_to(self, event_bus: EventBus) -> None:
        event_bus.subscribe(SignalGeneratedEvent, self._on_signal_generated)
        event_bus.subscribe(OrderFilledEvent, self._on_order_filled)
        event_bus.subscribe(PositionUpdatedEvent, self._on_position_updated)
        event_bus.subscribe(MarketDataReceivedEvent, self._on_market_data)

    @property
    def state(self) -> CurrentSignalState:
        return self._state

    @property
    def tracker(self) -> DummyTradeTracker:
        return self._tracker

    @property
    def signals_sent_today(self) -> int:
        return self._filter.signals_sent_today

    @property
    def last_exported_report_path(self) -> Path | None:
        return self._last_exported_report_path

    def export_report_now(self, as_of: datetime | None = None) -> Path:
        """On-demand export (e.g. for a demo, or reviewing progress mid-session) - the
        automatic end-of-day export in `_on_market_data` uses the exact same function."""
        report = self._tracker.build_daily_report(as_of or datetime.now())
        path = export_daily_report_json(report, directory=self._reports_directory)
        self._last_exported_report_path = path
        return path

    def _on_signal_generated(self, event: SignalGeneratedEvent) -> None:
        self._last_evaluation_by_strategy[event.evaluation.strategy_name] = event.evaluation
        self._state.market_bias = event.evaluation.direction

    def _on_market_data(self, event: MarketDataReceivedEvent) -> None:
        self._latest_candle_at = event.candle.timestamp
        candle_date = event.candle.timestamp.date().isoformat()
        status = classify_session(event.candle.timestamp)
        self._state.market_status = status

        if status == SessionPhase.OPEN:
            self._market_open_seen_on_date = candle_date
            return

        if (
            status == SessionPhase.CLOSED
            and self._market_open_seen_on_date == candle_date
            and self._report_generated_for_date != candle_date
        ):
            self._report_generated_for_date = candle_date
            report = self._tracker.build_daily_report(event.candle.timestamp)
            self._notifications.send_daily_summary(report)
            self._last_exported_report_path = export_daily_report_json(
                report, directory=self._reports_directory
            )

    def _on_order_filled(self, event: OrderFilledEvent) -> None:
        order = event.order
        evaluation = self._last_evaluation_by_strategy.get(order.strategy_name)
        if evaluation is None:
            logger.warning(
                "SignalService: no cached StrategyEvaluation for %s - skipping signal reporting",
                order.strategy_name,
            )
            return

        entry_price = order.average_fill_price or order.requested_price
        guardian_score = compute_guardian_score(
            evaluation, entry_price=entry_price, stop_loss=order.stop_loss, target=order.target
        )
        now = self._latest_candle_at or order.updated_at

        decision = self._filter.should_emit(
            strategy_name=order.strategy_name, guardian_score=guardian_score, now=now
        )
        if not decision.allowed:
            logger.info("SignalService: signal suppressed - %s", decision.reason)
            self._maybe_notify_no_trade(guardian_score, now, decision.reason)
            return

        signal_type = (
            SignalType.BUY_CE if order.direction == StrategyDirection.LONG else SignalType.BUY_PE
        )

        trade = self._tracker.open_trade(
            strategy_name=order.strategy_name,
            direction=order.direction,
            guardian_score=guardian_score,
            entry_price=entry_price,
            stop_loss=order.stop_loss,
            target=order.target,
            quantity=order.filled_quantity,
            opened_at=now,
        )
        self._pending_trade_by_strategy[order.strategy_name] = trade.trade_id

        self._state.latest_signal_type = signal_type
        self._state.latest_guardian_score = guardian_score
        self._state.latest_explanation = "; ".join(guardian_score.reasons)
        self._state.latest_signal_at = now
        self._state.latest_entry_price = entry_price
        self._state.latest_stop_loss = order.stop_loss
        self._state.latest_target = order.target

        self._notifications.send_signal(signal_type, trade)
        self._filter.record_emitted(strategy_name=order.strategy_name, now=now)

    def _maybe_notify_no_trade(
        self, guardian_score: GuardianScore, now: datetime, reason: str
    ) -> None:
        if "below threshold" not in reason:
            return
        cooldown_elapsed = (
            self._last_no_trade_notified_at is None
            or (now - self._last_no_trade_notified_at).total_seconds()
            >= self._config.cooldown_minutes * 60
        )
        if not cooldown_elapsed:
            return
        self._last_no_trade_notified_at = now
        self._notifications.send_no_trade(guardian_score, reason)

    def _on_position_updated(self, event: PositionUpdatedEvent) -> None:
        position = event.position

        if (
            position.status == PositionStatus.OPEN
            and position.strategy_name in self._pending_trade_by_strategy
        ):
            trade_id = self._pending_trade_by_strategy.pop(position.strategy_name)
            self._position_id_to_trade_id[position.position_id] = trade_id
            return

        if position.status != PositionStatus.CLOSED:
            return

        closing_trade_id = self._position_id_to_trade_id.get(position.position_id)
        if closing_trade_id is None:
            return
        del self._position_id_to_trade_id[position.position_id]

        trade = self._tracker.get(closing_trade_id)
        exit_price = _infer_exit_price(
            direction=position.direction,
            entry_price=trade.entry_price,
            realized_pnl=position.realized_pnl,
            initial_quantity=position.initial_quantity,
        )
        closed = self._tracker.close_trade(
            closing_trade_id,
            exit_price=exit_price,
            closed_at=self._latest_candle_at or position.closed_at or datetime.now(),
            pnl=position.realized_pnl,
        )

        if closed.exit_reason is not None:
            notification_type = _EXIT_REASON_TO_NOTIFICATION_SIGNAL_TYPE.get(closed.exit_reason)
            if notification_type is not None:
                self._notifications.send_exit(notification_type, closed)
