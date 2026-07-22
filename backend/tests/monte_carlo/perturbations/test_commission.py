import pytest
from pydantic import ValidationError

from app.monte_carlo.perturbations import commission
from app.monte_carlo.perturbations.commission import CommissionConfig
from tests.monte_carlo.helpers import make_trade


def test_flat_commission_is_subtracted_from_pnl() -> None:
    trade = make_trade(entry_price=100.0, exit_price=110.0, quantity=10)  # pnl=100.0
    config = CommissionConfig(flat_commission_per_trade=20.0)

    adjusted = commission.apply([trade], config)[0]

    assert adjusted.pnl == pytest.approx(80.0)


def test_percent_commission_scales_with_notional() -> None:
    trade = make_trade(entry_price=100.0, exit_price=110.0, quantity=10)  # notional=2100
    config = CommissionConfig(commission_percent=1.0)

    adjusted = commission.apply([trade], config)[0]

    expected_cost = 2100.0 * 0.01
    assert adjusted.pnl == pytest.approx(trade.pnl - expected_cost)


def test_flat_and_percent_commission_combine() -> None:
    trade = make_trade(entry_price=100.0, exit_price=110.0, quantity=10)
    config = CommissionConfig(commission_percent=1.0, flat_commission_per_trade=5.0)

    adjusted = commission.apply([trade], config)[0]

    expected_cost = 2100.0 * 0.01 + 5.0
    assert adjusted.pnl == pytest.approx(trade.pnl - expected_cost)


def test_zero_commission_leaves_pnl_unchanged() -> None:
    trade = make_trade()

    adjusted = commission.apply([trade], CommissionConfig())[0]

    assert adjusted.pnl == trade.pnl


def test_prices_and_quantity_are_unchanged() -> None:
    trade = make_trade(entry_price=100.0, exit_price=110.0, quantity=10)
    config = CommissionConfig(flat_commission_per_trade=20.0)

    adjusted = commission.apply([trade], config)[0]

    assert adjusted.entry_price == trade.entry_price
    assert adjusted.exit_price == trade.exit_price
    assert adjusted.quantity == trade.quantity


def test_rejects_negative_commission() -> None:
    with pytest.raises(ValidationError):
        CommissionConfig(commission_percent=-1.0)
