from datetime import datetime

import pytest

from app.paper_trading.event_bus import EventBus
from app.paper_trading.events import DomainEvent, MarketDataReceivedEvent, SignalGeneratedEvent
from tests.paper_trading.helpers import make_candle, make_strategy_evaluation


def test_handler_receives_published_event() -> None:
    bus = EventBus()
    received: list[MarketDataReceivedEvent] = []
    bus.subscribe(MarketDataReceivedEvent, received.append)

    event = MarketDataReceivedEvent(event_id="1", timestamp=datetime.now(), candle=make_candle())
    bus.publish(event)

    assert received == [event]


def test_handler_only_receives_its_exact_subscribed_type() -> None:
    bus = EventBus()
    received: list[MarketDataReceivedEvent] = []
    bus.subscribe(MarketDataReceivedEvent, received.append)

    signal_event = SignalGeneratedEvent(
        event_id="2", timestamp=datetime.now(), evaluation=make_strategy_evaluation()
    )
    bus.publish(signal_event)

    assert received == []


def test_multiple_handlers_are_all_called_in_subscription_order() -> None:
    bus = EventBus()
    call_order = []
    bus.subscribe(MarketDataReceivedEvent, lambda e: call_order.append("first"))
    bus.subscribe(MarketDataReceivedEvent, lambda e: call_order.append("second"))

    bus.publish(
        MarketDataReceivedEvent(event_id="1", timestamp=datetime.now(), candle=make_candle())
    )

    assert call_order == ["first", "second"]


def test_publish_with_no_subscribers_does_not_raise() -> None:
    bus = EventBus()
    bus.publish(
        MarketDataReceivedEvent(event_id="1", timestamp=datetime.now(), candle=make_candle())
    )


def test_handler_count_reflects_subscriptions() -> None:
    bus = EventBus()
    assert bus.handler_count(MarketDataReceivedEvent) == 0

    bus.subscribe(MarketDataReceivedEvent, lambda e: None)
    bus.subscribe(MarketDataReceivedEvent, lambda e: None)

    assert bus.handler_count(MarketDataReceivedEvent) == 2


def test_handler_exception_propagates_to_publisher() -> None:
    bus = EventBus()

    def failing_handler(event: DomainEvent) -> None:
        raise RuntimeError("boom")

    bus.subscribe(MarketDataReceivedEvent, failing_handler)

    with pytest.raises(RuntimeError, match="boom"):
        bus.publish(
            MarketDataReceivedEvent(event_id="1", timestamp=datetime.now(), candle=make_candle())
        )
