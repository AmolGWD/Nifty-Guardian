from datetime import datetime
from pathlib import Path

from app.paper_trading.event_bus import EventBus
from app.paper_trading.events import (
    MarketDataReceivedEvent,
    OrderFilledEvent,
    PositionUpdatedEvent,
    SignalGeneratedEvent,
)
from app.paper_trading.models import PositionStatus
from app.signals.models import (
    DailyPerformanceReport,
    DummyTrade,
    GuardianScore,
    SignalConfig,
    SignalType,
)
from app.signals.signal_filter import SessionPhase
from app.signals.signal_service import SignalService
from app.trading.strategy.models import StrategyDirection, StrategyStrength
from tests.signals.helpers import make_candle, make_evaluation, make_order, make_position


class FakeNotificationSink:
    def __init__(self) -> None:
        self.signals: list[tuple[SignalType, DummyTrade]] = []
        self.exits: list[tuple[SignalType, DummyTrade]] = []
        self.no_trades: list[tuple[GuardianScore, str]] = []
        self.daily_summaries: list[DailyPerformanceReport] = []

    def send_signal(self, signal_type: SignalType, trade: DummyTrade) -> None:
        self.signals.append((signal_type, trade))

    def send_exit(self, signal_type: SignalType, trade: DummyTrade) -> None:
        self.exits.append((signal_type, trade))

    def send_no_trade(self, guardian_score: GuardianScore, reason: str) -> None:
        self.no_trades.append((guardian_score, reason))

    def send_daily_summary(self, report: DailyPerformanceReport) -> None:
        self.daily_summaries.append(report)


def _build(
    *, reports_directory: Path | None = None, **config_overrides: object
) -> tuple[SignalService, EventBus, FakeNotificationSink]:
    base: dict[str, object] = dict(
        _env_file=None, confidence_threshold=0.0, cooldown_minutes=0.0, max_signals_per_day=100
    )
    base.update(config_overrides)
    sink = FakeNotificationSink()
    service = SignalService(
        config=SignalConfig(**base),  # type: ignore[arg-type]
        notification_service=sink,
        reports_directory=reports_directory,
    )
    bus = EventBus()
    service.subscribe_to(bus)
    return service, bus, sink


def _open_and_fill(
    bus: EventBus,
    *,
    candle_time: datetime = datetime(2026, 1, 5, 9, 30),
    evaluation_overrides: dict[str, object] | None = None,
    order_overrides: dict[str, object] | None = None,
    position_overrides: dict[str, object] | None = None,
) -> None:
    bus.publish(
        MarketDataReceivedEvent(
            event_id="e0", timestamp=datetime.now(), candle=make_candle(timestamp=candle_time)
        )
    )
    bus.publish(
        SignalGeneratedEvent(
            event_id="e1",
            timestamp=datetime.now(),
            evaluation=make_evaluation(**(evaluation_overrides or {})),
        )
    )
    bus.publish(
        OrderFilledEvent(
            event_id="e2",
            timestamp=datetime.now(),
            order=make_order(
                updated_at=candle_time, created_at=candle_time, **(order_overrides or {})
            ),
        )
    )
    bus.publish(
        PositionUpdatedEvent(
            event_id="e3",
            timestamp=datetime.now(),
            position=make_position(
                status=PositionStatus.OPEN, opened_at=candle_time, **(position_overrides or {})
            ),
        )
    )


def test_order_filled_with_no_cached_evaluation_is_skipped() -> None:
    service, bus, sink = _build()

    bus.publish(OrderFilledEvent(event_id="e1", timestamp=datetime.now(), order=make_order()))

    assert service.tracker.all_trades() == []
    assert sink.signals == []


def test_a_filled_order_opens_a_dummy_trade_and_sends_a_signal() -> None:
    service, bus, sink = _build()

    _open_and_fill(bus)

    trades = service.tracker.all_trades()
    assert len(trades) == 1
    assert trades[0].entry_price == 100.0
    assert trades[0].stop_loss == 95.0
    assert trades[0].target == 115.0
    assert len(sink.signals) == 1
    assert sink.signals[0][0] == SignalType.BUY_CE

    assert service.state.latest_entry_price == 100.0
    assert service.state.latest_stop_loss == 95.0
    assert service.state.latest_target == 115.0
    assert service.state.latest_signal_type == SignalType.BUY_CE


def test_market_status_reflects_the_latest_candle_session_phase() -> None:
    service, bus, _ = _build()

    bus.publish(
        MarketDataReceivedEvent(
            event_id="e1",
            timestamp=datetime.now(),
            candle=make_candle(timestamp=datetime(2026, 1, 5, 8, 0)),
        )
    )
    status_after_pre_market: SessionPhase | None = service.state.market_status
    assert status_after_pre_market == SessionPhase.PRE_MARKET

    bus.publish(
        MarketDataReceivedEvent(
            event_id="e2",
            timestamp=datetime.now(),
            candle=make_candle(timestamp=datetime(2026, 1, 5, 10, 0)),
        )
    )
    status_after_open: SessionPhase | None = service.state.market_status
    assert status_after_open == SessionPhase.OPEN

    bus.publish(
        MarketDataReceivedEvent(
            event_id="e3",
            timestamp=datetime.now(),
            candle=make_candle(timestamp=datetime(2026, 1, 5, 16, 0)),
        )
    )
    status_after_close: SessionPhase | None = service.state.market_status
    assert status_after_close == SessionPhase.CLOSED


def test_market_bias_updates_from_signal_generated_events() -> None:
    service, bus, _ = _build()

    bus.publish(
        SignalGeneratedEvent(event_id="e1", timestamp=datetime.now(), evaluation=make_evaluation())
    )

    assert service.state.market_bias.value == "Long"


def test_low_confidence_signal_is_suppressed_and_reported_as_no_trade() -> None:
    service, bus, sink = _build(confidence_threshold=95.0)

    _open_and_fill(bus, evaluation_overrides={"strength": StrategyStrength.WEAK})

    assert service.tracker.all_trades() == []
    assert sink.signals == []
    assert len(sink.no_trades) == 1


def test_position_closing_closes_the_matching_dummy_trade() -> None:
    service, bus, sink = _build()
    _open_and_fill(bus)

    trade_id = service.tracker.all_trades()[0].trade_id
    bus.publish(
        MarketDataReceivedEvent(
            event_id="e4",
            timestamp=datetime.now(),
            candle=make_candle(timestamp=datetime(2026, 1, 5, 11, 0)),
        )
    )
    bus.publish(
        PositionUpdatedEvent(
            event_id="e5",
            timestamp=datetime.now(),
            position=make_position(
                # entry=100, target=115, quantity=50 -> hitting target realizes (115-100)*50=750
                status=PositionStatus.CLOSED,
                realized_pnl=750.0,
                quantity=0,
                closed_at=datetime(2026, 1, 5, 11, 0),
            ),
        )
    )

    closed = service.tracker.get(trade_id)
    assert closed.status.value == "Closed"
    assert closed.pnl == 750.0
    assert len(sink.exits) == 1
    assert sink.exits[0][0] == SignalType.TARGET_HIT


def test_a_short_signal_opens_a_dummy_trade_with_the_short_geometry() -> None:
    service, bus, sink = _build()

    _open_and_fill(
        bus,
        evaluation_overrides={"direction": StrategyDirection.SHORT},
        order_overrides={
            "direction": StrategyDirection.SHORT, "stop_loss": 105.0, "target": 90.0,
        },
        position_overrides={"direction": StrategyDirection.SHORT},
    )

    trades = service.tracker.all_trades()
    assert len(trades) == 1
    assert trades[0].direction == StrategyDirection.SHORT
    assert trades[0].entry_price == 100.0
    # SHORT: stop-loss sits above entry, target sits below - the opposite
    # of LONG's geometry, priced this way by the (frozen) Risk Engine.
    assert trades[0].stop_loss == 105.0
    assert trades[0].target == 90.0
    assert len(sink.signals) == 1
    assert sink.signals[0][0] == SignalType.BUY_PE

    assert service.state.latest_signal_type == SignalType.BUY_PE


def test_short_position_closing_on_target_closes_the_matching_dummy_trade() -> None:
    service, bus, sink = _build()
    _open_and_fill(
        bus,
        evaluation_overrides={"direction": StrategyDirection.SHORT},
        order_overrides={
            "direction": StrategyDirection.SHORT, "stop_loss": 105.0, "target": 90.0,
        },
        position_overrides={"direction": StrategyDirection.SHORT},
    )

    trade_id = service.tracker.all_trades()[0].trade_id
    bus.publish(
        MarketDataReceivedEvent(
            event_id="e4",
            timestamp=datetime.now(),
            candle=make_candle(timestamp=datetime(2026, 1, 5, 11, 0)),
        )
    )
    bus.publish(
        PositionUpdatedEvent(
            event_id="e5",
            timestamp=datetime.now(),
            position=make_position(
                direction=StrategyDirection.SHORT,
                # SHORT, entry=100, exit=target=90, qty=50 -> pnl=(90-100)*50*-1=500
                status=PositionStatus.CLOSED,
                realized_pnl=500.0,
                quantity=0,
                closed_at=datetime(2026, 1, 5, 11, 0),
            ),
        )
    )

    closed = service.tracker.get(trade_id)
    assert closed.status.value == "Closed"
    assert closed.exit_price == 90.0
    assert closed.pnl == 500.0
    assert closed.exit_reason is not None
    assert closed.exit_reason.value == "Target"
    assert len(sink.exits) == 1
    assert sink.exits[0][0] == SignalType.TARGET_HIT


def test_short_position_closing_on_stoploss_closes_the_matching_dummy_trade() -> None:
    service, bus, sink = _build()
    _open_and_fill(
        bus,
        evaluation_overrides={"direction": StrategyDirection.SHORT},
        order_overrides={
            "direction": StrategyDirection.SHORT, "stop_loss": 105.0, "target": 90.0,
        },
        position_overrides={"direction": StrategyDirection.SHORT},
    )

    trade_id = service.tracker.all_trades()[0].trade_id
    bus.publish(
        MarketDataReceivedEvent(
            event_id="e4",
            timestamp=datetime.now(),
            candle=make_candle(timestamp=datetime(2026, 1, 5, 11, 0)),
        )
    )
    bus.publish(
        PositionUpdatedEvent(
            event_id="e5",
            timestamp=datetime.now(),
            position=make_position(
                direction=StrategyDirection.SHORT,
                # SHORT, entry=100, exit=stop_loss=105, qty=50 -> pnl=(105-100)*50*-1=-250
                status=PositionStatus.CLOSED,
                realized_pnl=-250.0,
                quantity=0,
                closed_at=datetime(2026, 1, 5, 11, 0),
            ),
        )
    )

    closed = service.tracker.get(trade_id)
    assert closed.status.value == "Closed"
    assert closed.exit_price == 105.0
    assert closed.pnl == -250.0
    assert closed.exit_reason is not None
    assert closed.exit_reason.value == "StopLoss"
    assert len(sink.exits) == 1
    assert sink.exits[0][0] == SignalType.STOPLOSS_HIT


def test_cooldown_prevents_a_second_signal_for_the_same_strategy() -> None:
    service, bus, sink = _build(cooldown_minutes=15.0)

    _open_and_fill(bus, candle_time=datetime(2026, 1, 5, 9, 30))
    assert len(sink.signals) == 1

    # A second signal 5 minutes later for the same strategy - still within cooldown.
    bus.publish(
        SignalGeneratedEvent(event_id="e6", timestamp=datetime.now(), evaluation=make_evaluation())
    )
    bus.publish(
        OrderFilledEvent(
            event_id="e7",
            timestamp=datetime.now(),
            order=make_order(
                order_id="order-2",
                updated_at=datetime(2026, 1, 5, 9, 35),
                created_at=datetime(2026, 1, 5, 9, 35),
            ),
        )
    )

    assert len(sink.signals) == 1


def test_daily_summary_fires_once_market_closes_after_being_open(tmp_path: Path) -> None:
    service, bus, sink = _build(reports_directory=tmp_path)

    bus.publish(
        MarketDataReceivedEvent(
            event_id="e1",
            timestamp=datetime.now(),
            candle=make_candle(timestamp=datetime(2026, 1, 5, 10, 0)),
        )
    )
    bus.publish(
        MarketDataReceivedEvent(
            event_id="e2",
            timestamp=datetime.now(),
            candle=make_candle(timestamp=datetime(2026, 1, 5, 16, 0)),
        )
    )

    assert len(sink.daily_summaries) == 1
    assert sink.daily_summaries[0].report_date == "2026-01-05"
    assert service.last_exported_report_path == tmp_path / "2026-01-05.json"
    assert (tmp_path / "2026-01-05.json").exists()


def test_daily_summary_does_not_fire_for_a_pre_market_only_candle() -> None:
    service, bus, sink = _build()

    bus.publish(
        MarketDataReceivedEvent(
            event_id="e1",
            timestamp=datetime.now(),
            candle=make_candle(timestamp=datetime(2026, 1, 5, 8, 0)),
        )
    )

    assert sink.daily_summaries == []


def test_export_report_now_writes_the_current_trade_history(tmp_path: Path) -> None:
    service, bus, _ = _build(reports_directory=tmp_path)
    _open_and_fill(bus)

    path = service.export_report_now(datetime(2026, 1, 5, 12, 0))

    assert path == tmp_path / "2026-01-05.json"
    assert path.exists()
    assert service.last_exported_report_path == path
