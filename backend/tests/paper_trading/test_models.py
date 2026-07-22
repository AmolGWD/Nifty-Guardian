from datetime import datetime

import pytest
from pydantic import ValidationError

from app.paper_trading.models import (
    ORDER_STATUS_TRANSITIONS,
    Order,
    OrderStatus,
    Portfolio,
    Position,
    PositionStatus,
)
from app.trading.strategy.models import StrategyDirection


def _make_order(**overrides: object) -> Order:
    now = datetime(2026, 1, 5, 9, 30)
    base = dict(
        order_id="order-1",
        strategy_name="EMABreakout",
        direction=StrategyDirection.LONG,
        requested_price=100.0,
        requested_quantity=10,
        stop_loss=95.0,
        target=110.0,
        created_at=now,
        updated_at=now,
    )
    base.update(overrides)
    return Order(**base)


def test_order_defaults_to_new_status() -> None:
    order = _make_order()
    assert order.status == OrderStatus.NEW
    assert order.filled_quantity == 0
    assert order.remaining_quantity == 10
    assert order.is_terminal is False


def test_terminal_statuses_have_no_outgoing_transitions() -> None:
    for status in (OrderStatus.FILLED, OrderStatus.CANCELLED, OrderStatus.REJECTED):
        assert ORDER_STATUS_TRANSITIONS[status] == frozenset()


def test_every_status_is_reachable_in_the_transition_table() -> None:
    reachable = {OrderStatus.NEW}
    for targets in ORDER_STATUS_TRANSITIONS.values():
        reachable |= targets
    assert reachable == set(OrderStatus)


def test_rejects_non_positive_requested_quantity() -> None:
    with pytest.raises(ValidationError, match="requested_quantity"):
        _make_order(requested_quantity=0)


def test_rejects_filled_quantity_exceeding_requested() -> None:
    with pytest.raises(ValidationError, match="filled_quantity"):
        _make_order(filled_quantity=20)


def test_order_is_immutable() -> None:
    order = _make_order()
    with pytest.raises(ValidationError):
        order.status = OrderStatus.FILLED  # type: ignore[misc]


def _make_position(**overrides: object) -> Position:
    base = dict(
        position_id="pos-1",
        strategy_name="EMABreakout",
        direction=StrategyDirection.LONG,
        average_entry_price=100.0,
        quantity=10,
        initial_quantity=10,
        realized_pnl=0.0,
        unrealized_pnl=0.0,
        status=PositionStatus.OPEN,
        opened_at=datetime(2026, 1, 5, 9, 30),
    )
    base.update(overrides)
    return Position(**base)


def test_position_rejects_quantity_exceeding_initial() -> None:
    with pytest.raises(ValidationError, match="quantity"):
        _make_position(quantity=20, initial_quantity=10)


def test_position_rejects_negative_quantity() -> None:
    with pytest.raises(ValidationError, match="quantity"):
        _make_position(quantity=-1)


def test_position_is_immutable() -> None:
    position = _make_position()
    with pytest.raises(ValidationError):
        position.quantity = 5  # type: ignore[misc]


def _make_portfolio(**overrides: object) -> Portfolio:
    base = dict(
        as_of=datetime(2026, 1, 5, 15, 30),
        cash=100_000.0,
        available_margin=100_000.0,
        open_position_ids=(),
        closed_position_ids=(),
        daily_pnl=0.0,
        total_equity=100_000.0,
        peak_equity=100_000.0,
    )
    base.update(overrides)
    return Portfolio(**base)


def test_drawdown_is_zero_when_equity_is_at_peak() -> None:
    portfolio = _make_portfolio(total_equity=100_000.0, peak_equity=100_000.0)
    assert portfolio.drawdown == 0.0
    assert portfolio.drawdown_percent == 0.0


def test_drawdown_reflects_decline_from_peak() -> None:
    portfolio = _make_portfolio(total_equity=90_000.0, peak_equity=100_000.0)
    assert portfolio.drawdown == 10_000.0
    assert portfolio.drawdown_percent == pytest.approx(10.0)


def test_portfolio_is_immutable() -> None:
    portfolio = _make_portfolio()
    with pytest.raises(ValidationError):
        portfolio.cash = 0.0  # type: ignore[misc]
