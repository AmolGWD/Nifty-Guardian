from datetime import datetime

from app.trading.conditions.no_trade_zone_filter import is_within_no_trade_zone
from app.trading.context.models import OverallMarketState
from tests.trading.conditions.helpers import make_market_context


def test_within_no_trade_zone_in_final_minutes_before_close() -> None:
    timestamp = datetime(2026, 7, 21, 15, 20)
    context = make_market_context(overall_state=OverallMarketState.RANGE_BOUND)

    assert is_within_no_trade_zone(timestamp, "15:30", 15, context) is True


def test_not_within_no_trade_zone_mid_day() -> None:
    timestamp = datetime(2026, 7, 21, 11, 0)
    context = make_market_context(overall_state=OverallMarketState.RANGE_BOUND)

    assert is_within_no_trade_zone(timestamp, "15:30", 15, context) is False


def test_within_no_trade_zone_when_market_is_volatile_range_mid_day() -> None:
    timestamp = datetime(2026, 7, 21, 11, 0)
    context = make_market_context(overall_state=OverallMarketState.VOLATILE_RANGE)

    assert is_within_no_trade_zone(timestamp, "15:30", 15, context) is True
