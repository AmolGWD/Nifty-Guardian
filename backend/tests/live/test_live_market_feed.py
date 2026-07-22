from app.live.live_market_feed import (
    LiveFeedMarketDataSource,
    ReplayMarketFeed,
    run_feed_in_background,
)
from tests.live.helpers import make_candles


def test_replay_market_feed_pushes_every_candle_to_subscribers() -> None:
    candles = make_candles(5)
    feed = ReplayMarketFeed(candles)
    received: list[object] = []
    feed.subscribe(received.append)

    feed.connect()
    feed.run()

    assert received == candles
    assert len(feed) == 5


def test_replay_market_feed_stops_pushing_once_disconnected() -> None:
    candles = make_candles(5)
    feed = ReplayMarketFeed(candles)
    received: list[object] = []

    def _callback(candle: object) -> None:
        received.append(candle)
        if len(received) == 2:
            feed.disconnect()

    feed.subscribe(_callback)
    feed.connect()
    feed.run()

    assert len(received) == 2


def test_live_feed_market_data_source_yields_every_pushed_candle() -> None:
    candles = make_candles(3)
    feed = ReplayMarketFeed(candles)
    source = LiveFeedMarketDataSource(feed, expected_length=3, queue_timeout_seconds=1.0)

    feed.connect()
    thread = run_feed_in_background(feed)
    collected = list(source)
    thread.join(timeout=2.0)

    assert collected == candles
    assert len(source) == 3


def test_live_feed_market_data_source_stops_early_on_disconnect_timeout() -> None:
    feed = ReplayMarketFeed([])
    feed.connect()
    feed.disconnect()
    source = LiveFeedMarketDataSource(feed, expected_length=10, queue_timeout_seconds=0.05)

    collected = list(source)

    assert collected == []
