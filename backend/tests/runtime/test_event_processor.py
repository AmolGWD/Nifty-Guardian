from datetime import datetime

from app.paper_trading.event_bus import EventBus
from app.paper_trading.order_manager import OrderManager
from app.paper_trading.paper_broker import PaperBroker
from app.paper_trading.portfolio_manager import PortfolioManager
from app.paper_trading.position_manager import PositionManager
from app.runtime.event_processor import EventProcessor
from app.trading.risk.models import RiskConfig
from app.trading.strategy.models import StrategyDirection
from app.trading.strategy.registry import default_registry
from tests.runtime.helpers import build_candles


def _make_processor(*, warmup_candles: int = 20) -> EventProcessor:
    event_bus = EventBus()
    position_manager = PositionManager(event_bus)
    portfolio_manager = PortfolioManager(
        initial_cash=100_000.0, position_manager=position_manager, event_bus=event_bus
    )
    order_manager = OrderManager(event_bus)
    return EventProcessor(
        event_bus=event_bus,
        order_manager=order_manager,
        position_manager=position_manager,
        portfolio_manager=portfolio_manager,
        broker=PaperBroker(),
        strategy_registry=default_registry(),
        risk_config=RiskConfig(),
        initial_capital=100_000.0,
        warmup_candles=warmup_candles,
    )


def test_process_candle_does_nothing_during_warmup() -> None:
    processor = _make_processor(warmup_candles=20)
    candles = build_candles(5)

    for candle in candles:
        processor.process_candle(candle, candles[: candles.index(candle) + 1])

    assert not processor.has_open_position


def test_process_candle_returns_a_non_negative_latency() -> None:
    processor = _make_processor()
    candles = build_candles(5)
    latency = processor.process_candle(candles[0], candles[:1])
    assert latency >= 0.0


def test_check_exit_prefers_stop_loss_over_target_when_both_breached() -> None:
    processor = _make_processor()
    position = processor._position_manager.open_position(
        strategy_name="EMABreakout",
        direction=StrategyDirection.LONG,
        entry_price=100.0,
        quantity=10,
    )
    processor._open_position_id = position.position_id
    processor._open_position_stop_loss = 95.0
    processor._open_position_target = 110.0

    candle = build_candles(1)[0].model_copy(update={"low": 90.0, "high": 120.0, "close": 100.0})
    processor._check_exit(candle)

    closed = processor._position_manager.get(position.position_id)
    # LONG, entry=100, exit=stop_loss=95, qty=10 -> realized_pnl = (95-100)*10 = -50
    assert closed.realized_pnl == -50.0
    assert processor._open_position_id is None


def test_check_exit_hits_target_when_stop_not_breached() -> None:
    processor = _make_processor()
    position = processor._position_manager.open_position(
        strategy_name="EMABreakout",
        direction=StrategyDirection.LONG,
        entry_price=100.0,
        quantity=10,
    )
    processor._open_position_id = position.position_id
    processor._open_position_stop_loss = 95.0
    processor._open_position_target = 110.0

    candle = build_candles(1)[0].model_copy(update={"low": 98.0, "high": 120.0, "close": 105.0})
    processor._check_exit(candle)

    closed = processor._position_manager.get(position.position_id)
    # LONG, entry=100, exit=target=110, qty=10 -> realized_pnl = (110-100)*10 = 100
    assert closed.realized_pnl == 100.0


def test_check_exit_closes_at_market_close_when_neither_breached() -> None:
    processor = _make_processor()
    position = processor._position_manager.open_position(
        strategy_name="EMABreakout",
        direction=StrategyDirection.LONG,
        entry_price=100.0,
        quantity=10,
    )
    processor._open_position_id = position.position_id
    processor._open_position_stop_loss = 95.0
    processor._open_position_target = 110.0

    eod_candle = build_candles(1)[0].model_copy(
        update={
            "low": 98.0, "high": 105.0, "close": 101.0,
            "timestamp": datetime(2026, 1, 5, 15, 30),
        }
    )
    processor._check_exit(eod_candle)

    closed = processor._position_manager.get(position.position_id)
    # LONG, entry=100, exit=close=101, qty=10 -> realized_pnl = (101-100)*10 = 10
    assert closed.realized_pnl == 10.0


def test_check_exit_leaves_position_open_when_no_condition_met() -> None:
    processor = _make_processor()
    position = processor._position_manager.open_position(
        strategy_name="EMABreakout",
        direction=StrategyDirection.LONG,
        entry_price=100.0,
        quantity=10,
    )
    processor._open_position_id = position.position_id
    processor._open_position_stop_loss = 95.0
    processor._open_position_target = 110.0

    mid_day_candle = build_candles(1)[0].model_copy(
        update={
            "low": 98.0, "high": 105.0, "close": 101.0,
            "timestamp": datetime(2026, 1, 5, 11, 0),
        }
    )
    processor._check_exit(mid_day_candle)

    assert processor._open_position_id == position.position_id


def test_check_exit_prefers_stop_loss_over_target_for_short_when_both_breached() -> None:
    processor = _make_processor()
    position = processor._position_manager.open_position(
        strategy_name="EMABreakout",
        direction=StrategyDirection.SHORT,
        entry_price=100.0,
        quantity=10,
    )
    processor._open_position_id = position.position_id
    processor._open_position_stop_loss = 105.0
    processor._open_position_target = 90.0

    candle = build_candles(1)[0].model_copy(update={"low": 80.0, "high": 110.0, "close": 100.0})
    processor._check_exit(candle)

    closed = processor._position_manager.get(position.position_id)
    # SHORT, entry=100, exit=stop_loss=105, qty=10 -> realized_pnl = (100-105)*10 = -50
    assert closed.realized_pnl == -50.0
    assert processor._open_position_id is None


def test_check_exit_hits_target_for_short_when_stop_not_breached() -> None:
    processor = _make_processor()
    position = processor._position_manager.open_position(
        strategy_name="EMABreakout",
        direction=StrategyDirection.SHORT,
        entry_price=100.0,
        quantity=10,
    )
    processor._open_position_id = position.position_id
    processor._open_position_stop_loss = 105.0
    processor._open_position_target = 90.0

    candle = build_candles(1)[0].model_copy(update={"low": 88.0, "high": 102.0, "close": 95.0})
    processor._check_exit(candle)

    closed = processor._position_manager.get(position.position_id)
    # SHORT, entry=100, exit=target=90, qty=10 -> realized_pnl = (100-90)*10 = 100
    assert closed.realized_pnl == 100.0


def test_check_exit_leaves_short_position_open_when_no_condition_met() -> None:
    processor = _make_processor()
    position = processor._position_manager.open_position(
        strategy_name="EMABreakout",
        direction=StrategyDirection.SHORT,
        entry_price=100.0,
        quantity=10,
    )
    processor._open_position_id = position.position_id
    processor._open_position_stop_loss = 105.0
    processor._open_position_target = 90.0

    mid_day_candle = build_candles(1)[0].model_copy(
        update={
            "low": 96.0, "high": 102.0, "close": 99.0,
            "timestamp": datetime(2026, 1, 5, 11, 0),
        }
    )
    processor._check_exit(mid_day_candle)

    assert processor._open_position_id == position.position_id


def test_day_boundary_resets_trade_counters() -> None:
    processor = _make_processor()
    processor._current_date = datetime(2026, 1, 5).date()
    processor._trades_taken_today = 3
    processor._realized_loss_today = 500.0

    next_day_candle = build_candles(1)[0].model_copy(
        update={"timestamp": datetime(2026, 1, 6, 9, 15)}
    )
    processor.process_candle(next_day_candle, [next_day_candle])

    assert processor._trades_taken_today == 0
    assert processor._realized_loss_today == 0.0
    assert processor._current_date == datetime(2026, 1, 6).date()


def test_same_day_candle_does_not_reset_counters() -> None:
    processor = _make_processor()
    processor._current_date = datetime(2026, 1, 5).date()
    processor._trades_taken_today = 3
    processor._realized_loss_today = 500.0

    same_day_candle = build_candles(1)[0].model_copy(
        update={"timestamp": datetime(2026, 1, 5, 10, 0)}
    )
    processor.process_candle(same_day_candle, [same_day_candle])

    assert processor._trades_taken_today == 3
    assert processor._realized_loss_today == 500.0
