from datetime import datetime

import pytest
from pydantic import ValidationError

from app.market_data.market_session import MarketSessionStatus
from app.trading.conditions.engine import build_trading_conditions
from app.trading.conditions.models import NoTradeReason, TradingConditions
from tests.trading.conditions.helpers import make_market_context

MARKET_OPEN = "09:15"
MARKET_CLOSE = "15:30"


def test_can_trade_during_normal_mid_day_conditions() -> None:
    conditions = build_trading_conditions(
        session_state=MarketSessionStatus.OPEN,
        current_timestamp=datetime(2026, 7, 21, 11, 0),  # Tuesday
        market_context=make_market_context(),
        market_open=MARKET_OPEN,
        market_close=MARKET_CLOSE,
    )

    assert isinstance(conditions, TradingConditions)
    assert conditions.can_trade is True
    assert conditions.no_trade_reason is None


def test_session_invalid_takes_priority_over_everything_else() -> None:
    conditions = build_trading_conditions(
        session_state=MarketSessionStatus.OPEN,
        current_timestamp=datetime(2026, 7, 25, 11, 0),  # Saturday
        market_context=make_market_context(),
        market_open=MARKET_OPEN,
        market_close=MARKET_CLOSE,
        has_open_position=True,
    )

    assert conditions.can_trade is False
    assert conditions.no_trade_reason == NoTradeReason.SESSION_INVALID


def test_blocked_within_opening_range() -> None:
    conditions = build_trading_conditions(
        session_state=MarketSessionStatus.OPEN,
        current_timestamp=datetime(2026, 7, 21, 9, 20),  # Tuesday, 5 min after open
        market_context=make_market_context(),
        market_open=MARKET_OPEN,
        market_close=MARKET_CLOSE,
        opening_range_minutes=15,
    )

    assert conditions.can_trade is False
    assert conditions.no_trade_reason == NoTradeReason.WITHIN_OPENING_RANGE
    assert conditions.opening_range_complete is False


def test_blocked_when_position_already_open() -> None:
    conditions = build_trading_conditions(
        session_state=MarketSessionStatus.OPEN,
        current_timestamp=datetime(2026, 7, 21, 11, 0),  # Tuesday
        market_context=make_market_context(),
        market_open=MARKET_OPEN,
        market_close=MARKET_CLOSE,
        has_open_position=True,
    )

    assert conditions.can_trade is False
    assert conditions.no_trade_reason == NoTradeReason.POSITION_ALREADY_OPEN
    assert conditions.position_guard_ok is False


def test_blocked_when_cooldown_active() -> None:
    conditions = build_trading_conditions(
        session_state=MarketSessionStatus.OPEN,
        current_timestamp=datetime(2026, 7, 21, 11, 0),  # Tuesday
        market_context=make_market_context(),
        market_open=MARKET_OPEN,
        market_close=MARKET_CLOSE,
        last_trade_closed_at=datetime(2026, 7, 21, 10, 58),
        cooldown_minutes=5,
    )

    assert conditions.can_trade is False
    assert conditions.no_trade_reason == NoTradeReason.COOLDOWN_ACTIVE
    assert conditions.cooldown_complete is False


def test_blocked_when_liquidity_insufficient() -> None:
    conditions = build_trading_conditions(
        session_state=MarketSessionStatus.OPEN,
        current_timestamp=datetime(2026, 7, 21, 11, 0),  # Tuesday
        market_context=make_market_context(),
        market_open=MARKET_OPEN,
        market_close=MARKET_CLOSE,
        volume=10,
        min_volume=500,
    )

    assert conditions.can_trade is False
    assert conditions.no_trade_reason == NoTradeReason.INSUFFICIENT_LIQUIDITY
    assert conditions.liquidity_ok is False


def test_blocked_on_expiry_day_when_disallowed() -> None:
    conditions = build_trading_conditions(
        session_state=MarketSessionStatus.OPEN,
        current_timestamp=datetime(2026, 7, 30, 11, 0),  # Thursday, expiry day
        market_context=make_market_context(),
        market_open=MARKET_OPEN,
        market_close=MARKET_CLOSE,
        expiry_date=datetime(2026, 7, 30).date(),
        allow_expiry_day_trading=False,
    )

    assert conditions.can_trade is False
    assert conditions.no_trade_reason == NoTradeReason.EXPIRY_NOT_ALLOWED
    assert conditions.expiry_allowed is False


def test_trading_conditions_is_immutable() -> None:
    conditions = build_trading_conditions(
        session_state=MarketSessionStatus.OPEN,
        current_timestamp=datetime(2026, 7, 21, 11, 0),
        market_context=make_market_context(),
        market_open=MARKET_OPEN,
        market_close=MARKET_CLOSE,
    )

    with pytest.raises(ValidationError):
        conditions.can_trade = False  # type: ignore[misc]
