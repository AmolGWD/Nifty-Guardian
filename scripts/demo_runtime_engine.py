#!/usr/bin/env python3
"""
Standalone demonstration of the Paper Trading Engine (Phase 20).

Replays 100 synthetic historical candles through `app.runtime` -
Startup -> RuntimeEngine (driven by a SynchronousScheduler) ->
Shutdown - printing session start, replay progress, every signal/order/
portfolio update as it happens, and a final summary.

This is a continuous replay loop, not a single hand-built decision (that
was `scripts/demo_paper_architecture.py`, Phase 19's demo) - but it is
still entirely replay-driven: no websocket, no Zerodha, no REST API, no
live connectivity of any kind. Run from anywhere:

    python3 scripts/demo_runtime_engine.py
"""

from __future__ import annotations

import sys
from datetime import datetime, timedelta
from pathlib import Path

_BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

from app.market_data.schemas import Candle  # noqa: E402
from app.paper_trading.events import (  # noqa: E402
    DomainEvent,
    OrderFilledEvent,
    OrderSubmittedEvent,
    PortfolioUpdatedEvent,
    SignalGeneratedEvent,
)
from app.runtime import (  # noqa: E402
    EngineConfig,
    ReplaySpeed,
    StaticListSource,
    shutdown_runtime,
    start_runtime,
)

CANDLE_COUNT = 100
PROGRESS_EVERY = 20


def _print_header(title: str) -> None:
    banner = "=" * 70
    print(f"\n{banner}\n{title}\n{banner}")


def build_sample_candles(n: int) -> list[Candle]:
    """
    n synthetic weekday-only 15-minute candles in a mild uptrend - enough
    to trigger the EMA breakout strategy after warmup, in the same style
    as scripts/demo_pipeline.py / scripts/demo_paper_architecture.py.
    """
    candles: list[Candle] = []
    timestamp = datetime(2026, 7, 20, 9, 15)  # a Monday
    close = 100.0
    count_today = 0

    while len(candles) < n:
        if timestamp.weekday() >= 5:
            timestamp += timedelta(days=1)
            continue

        open_price = close
        close = close - 1.0 if len(candles) % 7 == 6 else close + 2.0
        high = max(open_price, close) + 1.0
        low = min(open_price, close) - 1.0
        volume = 10_000 + (len(candles) * 250)
        candles.append(
            Candle(
                timestamp=timestamp, open=open_price, high=high, low=low, close=close,
                volume=volume,
            )
        )
        timestamp += timedelta(minutes=15)
        count_today += 1
        if count_today >= 25:
            timestamp += timedelta(hours=16)
            count_today = 0

    return candles


def main() -> None:
    _print_header("SESSION START")
    candles = build_sample_candles(CANDLE_COUNT)
    print(f"Loaded {len(candles)} synthetic candles ({candles[0].timestamp} -> "
          f"{candles[-1].timestamp})")

    config = EngineConfig(replay_speed=ReplaySpeed.UNLIMITED, maximum_candles=CANDLE_COUNT)
    context = start_runtime(
        config=config,
        market_data_source=StaticListSource(candles),
        initial_capital=100_000.0,
    )
    print(f"Session state: {context.session_controller.state.value}")

    def _log_signal(event: DomainEvent) -> None:
        assert isinstance(event, SignalGeneratedEvent)
        evaluation = event.evaluation
        print(
            f"  [SIGNAL] {evaluation.strategy_name}: valid={evaluation.valid} "
            f"direction={evaluation.direction.value} strength={evaluation.strength.value}"
        )

    def _log_order_submitted(event: DomainEvent) -> None:
        assert isinstance(event, OrderSubmittedEvent)
        order = event.order
        print(
            f"  [ORDER SUBMITTED] {order.strategy_name} {order.direction.value} "
            f"qty={order.requested_quantity} @ {order.requested_price}"
        )

    def _log_order_filled(event: DomainEvent) -> None:
        assert isinstance(event, OrderFilledEvent)
        order = event.order
        print(
            f"  [ORDER FILLED] {order.strategy_name} filled {order.filled_quantity} @ "
            f"{order.average_fill_price}"
        )

    def _log_portfolio(event: DomainEvent) -> None:
        assert isinstance(event, PortfolioUpdatedEvent)
        portfolio = event.portfolio
        if context.engine.processed_count % PROGRESS_EVERY == 0:
            print(
                f"  [PORTFOLIO @ candle {context.engine.processed_count}] "
                f"cash={portfolio.cash} total_equity={portfolio.total_equity} "
                f"open_positions={len(portfolio.open_position_ids)}"
            )

    context.event_bus.subscribe(SignalGeneratedEvent, _log_signal)
    context.event_bus.subscribe(OrderSubmittedEvent, _log_order_submitted)
    context.event_bus.subscribe(OrderFilledEvent, _log_order_filled)
    context.event_bus.subscribe(PortfolioUpdatedEvent, _log_portfolio)

    _print_header("REPLAY PROGRESS")
    context.engine.run()
    print(f"\nProcessed {context.engine.processed_count} of {len(candles)} candles.")

    summary = shutdown_runtime(context)

    _print_header("EXECUTION JOURNAL (last 10 entries)")
    for entry in summary.journaled_entries[-10:]:
        print(f"  {entry.entry_type.value}: {entry.description[:80]}")

    _print_header("Demo complete - no real trade executed, no live connectivity used")


if __name__ == "__main__":
    main()
