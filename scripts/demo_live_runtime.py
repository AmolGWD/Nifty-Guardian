#!/usr/bin/env python3
"""
Standalone demonstration of Live Trading Mode (Phase 24).

Wires the frozen Runtime Engine + this phase's Live Market Feed
abstraction + a mocked broker together via `start_live_runtime()`, and
drives the resulting `LiveSession` through connect, heartbeat,
receiving candles, generating and executing an order, pause, resume,
disconnect, and an emergency stop. The market feed is a `ReplayMarketFeed`
over synthetic candles and the broker is a hand-built fake - no real
credentials, no real network access, no real order ever placed.

Run from anywhere:

    python3 scripts/demo_live_runtime.py
"""

from __future__ import annotations

import sys
from datetime import datetime, timedelta
from pathlib import Path

_BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

from app.live import (  # noqa: E402
    LiveConfig,
    ReplayMarketFeed,
    run_feed_in_background,
    start_live_runtime,
)
from app.market_data.schemas import Candle  # noqa: E402
from app.paper_trading.models import Order, OrderStatus  # noqa: E402
from app.trading.strategy.models import StrategyDirection  # noqa: E402


def _print_header(title: str) -> None:
    banner = "=" * 70
    print(f"\n{banner}\n{title}\n{banner}")


def _build_candles(n: int) -> list[Candle]:
    start = datetime(2026, 1, 5, 9, 15)
    close = 100.0
    candles = []
    for i in range(n):
        open_price = close
        close = close + 2.0
        candles.append(
            Candle(
                timestamp=start + timedelta(minutes=15 * i),
                open=open_price,
                high=max(open_price, close) + 1.0,
                low=min(open_price, close) - 1.0,
                close=close,
                volume=10_000,
            )
        )
    return candles


class DemoBroker:
    """A hand-built `BrokerInterface` fake - fills every order instantly, never rejects."""

    def __init__(self) -> None:
        self.submitted: list[Order] = []
        self.cancelled: list[Order] = []

    def submit_order(self, order: Order) -> Order:
        self.submitted.append(order)
        return order.model_copy(
            update={
                "status": OrderStatus.FILLED,
                "filled_quantity": order.requested_quantity,
                "average_fill_price": order.requested_price,
            }
        )

    def cancel_order(self, order: Order) -> Order:
        self.cancelled.append(order)
        return order.model_copy(update={"status": OrderStatus.CANCELLED})


def main() -> None:
    candles = _build_candles(5)
    feed = ReplayMarketFeed(candles, delay_seconds=0.05)
    broker = DemoBroker()
    config = LiveConfig(live_mode=False)

    _print_header("1. WIRE THE LIVE RUNTIME (Runtime Engine + Live Market Feed + Broker Adapter)")
    context = start_live_runtime(
        market_feed=feed,
        broker=broker,
        expected_candle_count=len(candles),
        config=config,
    )
    print(f"  LiveConfig.live_mode = {config.live_mode} (paper-safe default)")
    print(f"  Session state: {context.live_session.state.value}")

    _print_header("2. CONNECT")
    state = context.live_session.connect()
    print(f"  Session state: {state.value}")

    _print_header("3. HEARTBEAT")
    for component in ("broker", "market_feed"):
        snapshot = context.heartbeat_monitor.snapshot(component)
        print(
            f"  {component}: stale={snapshot.is_stale}, "
            f"last_seen_seconds_ago={snapshot.last_seen_seconds_ago:.3f}"
        )

    _print_header("4. START TRADING AND RECEIVE CANDLES")
    context.live_session.start_trading()
    feed.connect()
    thread = run_feed_in_background(feed)
    context.runtime_engine.run()
    thread.join(timeout=5.0)
    processed = context.runtime_engine.processed_count
    print(f"  Candles processed by the frozen RuntimeEngine: {processed}")

    _print_header("5. GENERATE AND EXECUTE AN ORDER (through OrderExecutor -> DemoBroker)")
    order = Order(
        order_id="demo-live-1",
        strategy_name="EMABreakout",
        direction=StrategyDirection.LONG,
        requested_price=104.0,
        requested_quantity=25,
        stop_loss=98.0,
        target=112.0,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    filled = context.order_executor.submit_order(order)
    print(f"  Order {filled.order_id}: status={filled.status.value}, qty={filled.filled_quantity}")
    tracked = context.order_executor.last_known_status(filled.order_id)
    assert tracked is not None
    print(f"  OrderExecutor.last_known_status: {tracked.status.value}")

    _print_header("6. PAUSE / RESUME")
    print(f"  pause():  {context.live_session.pause().value}")
    print(f"  resume(): {context.live_session.resume().value}")

    _print_header("7. SAFETY CHECK BEFORE THE NEXT ORDER")
    decision = context.safety_manager.check_before_order(datetime.now().time())
    print(f"  gate={decision.gate}, allowed={decision.allowed}, reason={decision.reason}")

    _print_header("8. DISCONNECT")
    print(f"  stop(): {context.live_session.stop().value}")

    _print_header("9. EMERGENCY STOP (on a fresh session)")
    feed2 = ReplayMarketFeed(_build_candles(2))
    context2 = start_live_runtime(
        market_feed=feed2,
        broker=DemoBroker(),
        expected_candle_count=2,
        config=LiveConfig(live_mode=False),
    )
    context2.live_session.connect()
    context2.live_session.start_trading()
    state = context2.live_session.emergency_stop("demo: simulated critical failure")
    print(f"  emergency_stop() -> {state.value}")
    print(f"  SafetyManager.is_emergency_stopped: {context2.safety_manager.is_emergency_stopped}")

    _print_header("Demo complete - no real broker connectivity used, no real order ever placed")


if __name__ == "__main__":
    main()
