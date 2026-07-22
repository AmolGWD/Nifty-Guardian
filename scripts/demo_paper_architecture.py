#!/usr/bin/env python3
"""
Standalone demonstration of the Paper Trading Architecture (Phase 19).

Drives the existing (frozen) Indicator/Context/Conditions/Strategy/
Risk pipeline against one hand-built candle snapshot - exactly as
`scripts/demo_pipeline.py` already does - then feeds that single
decision through the new event-driven paper trading pieces: an
EventBus, an OrderManager backed by PaperBroker (simulated fill only),
a PositionManager, and a PortfolioManager, with an ExecutionJournal and
PerformanceMonitor observing every event as it happens.

This demonstrates the architecture end to end for one decision - it is
NOT a continuous trading loop (that is the Paper Trading Engine, the
next, not-yet-authorized phase), does NOT connect to Zerodha, and does
NOT execute any real trade. Run from anywhere:

    python3 scripts/demo_paper_architecture.py
"""

from __future__ import annotations

import sys
import uuid
from datetime import datetime, timedelta
from pathlib import Path

_BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

from app.market_data.market_session import MarketSessionStatus  # noqa: E402
from app.market_data.schemas import Candle  # noqa: E402
from app.paper_trading.event_bus import EventBus  # noqa: E402
from app.paper_trading.events import (  # noqa: E402
    DomainEvent,
    MarketDataReceivedEvent,
    OrderFilledEvent,
    OrderSubmittedEvent,
    PortfolioUpdatedEvent,
    PositionUpdatedEvent,
    RiskApprovedEvent,
    SignalGeneratedEvent,
)
from app.paper_trading.execution_journal import ExecutionJournal  # noqa: E402
from app.paper_trading.order_manager import OrderManager  # noqa: E402
from app.paper_trading.paper_broker import PaperBroker  # noqa: E402
from app.paper_trading.performance_monitor import PerformanceMonitor  # noqa: E402
from app.paper_trading.portfolio_manager import PortfolioManager  # noqa: E402
from app.paper_trading.position_manager import PositionManager  # noqa: E402
from app.trading.conditions.engine import build_trading_conditions  # noqa: E402
from app.trading.context.engine import build_market_context  # noqa: E402
from app.trading.indicators.engine import calculate_indicator_snapshot  # noqa: E402
from app.trading.risk.engine import build_risk_assessment  # noqa: E402
from app.trading.risk.models import CapitalState, RiskConfig  # noqa: E402
from app.trading.strategy.engine import run_strategies  # noqa: E402
from app.trading.strategy.registry import default_registry  # noqa: E402

MARKET_OPEN = "09:15"
MARKET_CLOSE = "15:30"


def _print_header(title: str) -> None:
    banner = "=" * 70
    print(f"\n{banner}\n{title}\n{banner}")


def build_sample_candles() -> list[Candle]:
    """25 synthetic 15-minute candles in a clear uptrend (see scripts/demo_pipeline.py)."""
    candles = []
    timestamp = datetime(2026, 7, 21, 9, 15)  # a Tuesday
    close = 100.0

    for i in range(25):
        open_price = close
        close = close - 1.0 if i % 6 == 5 else close + 2.5
        high = max(open_price, close) + 1.0
        low = min(open_price, close) - 1.0
        volume = 10_000 + (i * 500)
        candles.append(
            Candle(
                timestamp=timestamp, open=open_price, high=high, low=low, close=close,
                volume=volume,
            )
        )
        timestamp += timedelta(minutes=15)

    return candles


def main() -> None:
    _print_header("EVENT SEQUENCE")
    bus = EventBus()
    journal = ExecutionJournal()
    journal.subscribe_to(bus)

    def _log(event: DomainEvent) -> None:
        print(f"  [{event.timestamp.strftime('%H:%M:%S')}] {type(event).__name__}")

    for event_type in (
        MarketDataReceivedEvent,
        SignalGeneratedEvent,
        RiskApprovedEvent,
    ):
        bus.subscribe(event_type, _log)

    position_manager = PositionManager(bus)
    portfolio_manager = PortfolioManager(
        initial_cash=100_000.0, position_manager=position_manager, event_bus=bus
    )
    order_manager = OrderManager(bus)
    broker = PaperBroker()
    performance_monitor = PerformanceMonitor(bus, initial_capital=100_000.0)

    for event_type in (
        OrderSubmittedEvent,
        OrderFilledEvent,
        PositionUpdatedEvent,
        PortfolioUpdatedEvent,
    ):
        bus.subscribe(event_type, _log)

    # --- 1. MarketData event: feed one hand-built candle snapshot through the
    # existing (frozen) Indicator/Context/Conditions/Strategy/Risk pipeline. ---
    candles = build_sample_candles()
    bus.publish(
        MarketDataReceivedEvent(
            event_id=str(uuid.uuid4()), timestamp=datetime.now(), candle=candles[-1]
        )
    )

    snapshot = calculate_indicator_snapshot(
        candles, total_call_oi=120_000, total_put_oi=180_000, price_change=5.0, oi_change=10.0
    )
    session_state = MarketSessionStatus.OPEN
    market_context = build_market_context(snapshot, session_state)
    trading_conditions = build_trading_conditions(
        session_state=session_state,
        current_timestamp=datetime(2026, 7, 21, 11, 0),
        market_context=market_context,
        market_open=MARKET_OPEN,
        market_close=MARKET_CLOSE,
    )

    # --- 2. Signal event ---
    registry = default_registry()
    evaluations = run_strategies(registry, snapshot, market_context, trading_conditions)
    evaluation = evaluations[0]
    bus.publish(
        SignalGeneratedEvent(
            event_id=str(uuid.uuid4()), timestamp=datetime.now(), evaluation=evaluation
        )
    )

    # --- 3. Risk approval ---
    risk_config = RiskConfig()
    capital_state = CapitalState(
        total_capital=100_000.0, capital_deployed=0.0, realized_loss_today=0.0,
        trades_taken_today=0, open_positions=0,
    )
    risk_assessment = build_risk_assessment(
        strategy_evaluation=evaluation, entry_price=snapshot.close_price, atr=snapshot.atr,
        config=risk_config, capital_state=capital_state,
    )
    bus.publish(
        RiskApprovedEvent(
            event_id=str(uuid.uuid4()), timestamp=datetime.now(), risk_assessment=risk_assessment
        )
    )

    if not (evaluation.valid and risk_assessment.risk_ok and risk_assessment.position_size >= 1):
        print("\nNo approved trade this run (strategy invalid or risk rejected) - stopping here.")
        return

    # --- 4. Paper order -> 5. Fill ---
    order = order_manager.create_order(
        strategy_name=evaluation.strategy_name,
        direction=evaluation.direction,
        requested_price=snapshot.close_price,
        requested_quantity=risk_assessment.position_size,
        stop_loss=risk_assessment.stop_loss,
        target=risk_assessment.target,
    )
    order_manager.validate(order.order_id)
    filled_order = order_manager.submit(order.order_id, broker)

    # --- 6. Position update ---
    position = position_manager.open_position(
        strategy_name=filled_order.strategy_name,
        direction=filled_order.direction,
        entry_price=filled_order.average_fill_price or filled_order.requested_price,
        quantity=filled_order.filled_quantity,
    )

    # --- 7. Portfolio update ---
    portfolio = portfolio_manager.snapshot()

    _print_header("FINAL STATE")
    print(f"Order: {filled_order.status.value}, filled {filled_order.filled_quantity} @ "
          f"{filled_order.average_fill_price}")
    print(f"Position: {position.status.value}, quantity={position.quantity}, "
          f"entry={position.average_entry_price}")
    print(f"Portfolio: cash={portfolio.cash}, total_equity={portfolio.total_equity}, "
          f"open_positions={len(portfolio.open_position_ids)}")

    _print_header("EXECUTION JOURNAL")
    for entry in journal.all_entries():
        print(f"  {entry.entry_type.value}: {entry.description[:80]}")

    _print_header("PERFORMANCE MONITOR")
    print(performance_monitor.snapshot())

    _print_header("Demo complete - no real trade executed, no live connectivity used")


if __name__ == "__main__":
    main()
