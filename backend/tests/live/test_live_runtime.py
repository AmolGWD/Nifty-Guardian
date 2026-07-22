from app.live.live_market_feed import ReplayMarketFeed, run_feed_in_background
from app.live.live_runtime import start_live_runtime
from app.live.models import LiveConfig, LiveSessionState
from app.paper_trading.models import OrderStatus
from tests.live.helpers import FakeBroker, make_candles, make_order


def test_start_live_runtime_wires_every_component() -> None:
    candles = make_candles(3)
    feed = ReplayMarketFeed(candles)
    broker = FakeBroker()
    config = LiveConfig(_env_file=None)

    context = start_live_runtime(
        market_feed=feed,
        broker=broker,
        expected_candle_count=len(candles),
        config=config,
    )

    assert context.live_session.state == LiveSessionState.INITIALIZING
    assert context.market_feed is feed


def test_session_lifecycle_through_the_wired_runtime_context() -> None:
    candles = make_candles(3)
    feed = ReplayMarketFeed(candles)
    broker = FakeBroker()
    context = start_live_runtime(
        market_feed=feed,
        broker=broker,
        expected_candle_count=len(candles),
        config=LiveConfig(_env_file=None),
    )

    assert context.live_session.connect() == LiveSessionState.CONNECTED
    assert context.live_session.start_trading() == LiveSessionState.TRADING
    assert context.heartbeat_monitor.seconds_since_last_seen("broker") is not None
    assert context.live_session.stop() == LiveSessionState.STOPPED


def test_order_executor_submits_through_to_the_wrapped_broker() -> None:
    candles = make_candles(1)
    feed = ReplayMarketFeed(candles)
    broker = FakeBroker()
    context = start_live_runtime(
        market_feed=feed,
        broker=broker,
        expected_candle_count=len(candles),
        config=LiveConfig(_env_file=None),
    )

    order = make_order()
    result = context.order_executor.submit_order(order)

    assert result.status == OrderStatus.FILLED
    assert broker.submit_calls == [order]


def test_runtime_engine_processes_candles_pushed_through_the_live_feed() -> None:
    candles = make_candles(5)
    feed = ReplayMarketFeed(candles)
    broker = FakeBroker()
    context = start_live_runtime(
        market_feed=feed,
        broker=broker,
        expected_candle_count=len(candles),
        config=LiveConfig(_env_file=None),
    )

    feed.connect()
    thread = run_feed_in_background(feed)
    context.runtime_engine.run()
    thread.join(timeout=2.0)

    assert context.runtime_engine.processed_count == 5
