import pytest
from pydantic import ValidationError

from app.monte_carlo.perturbations import slippage
from app.monte_carlo.perturbations.slippage import SlippageConfig
from app.trading.strategy.models import StrategyDirection
from tests.monte_carlo.helpers import make_trade


def test_long_entry_slippage_worsens_entry_price() -> None:
    trade = make_trade(entry_price=100.0, exit_price=110.0, quantity=10)
    config = SlippageConfig(entry_slippage_percent=1.0, exit_slippage_percent=0.0)

    adjusted = slippage.apply([trade], config)[0]

    assert adjusted.entry_price == pytest.approx(101.0)


def test_long_exit_slippage_worsens_exit_price() -> None:
    trade = make_trade(entry_price=100.0, exit_price=110.0, quantity=10)
    config = SlippageConfig(entry_slippage_percent=0.0, exit_slippage_percent=1.0)

    adjusted = slippage.apply([trade], config)[0]

    assert adjusted.exit_price == pytest.approx(108.9)


def test_short_entry_slippage_worsens_entry_price_the_other_direction() -> None:
    trade = make_trade(
        entry_price=100.0, exit_price=90.0, quantity=10, direction=StrategyDirection.SHORT
    )
    config = SlippageConfig(entry_slippage_percent=1.0, exit_slippage_percent=0.0)

    adjusted = slippage.apply([trade], config)[0]

    assert adjusted.entry_price == pytest.approx(99.0)


def test_pnl_is_recomputed_from_adjusted_prices() -> None:
    trade = make_trade(entry_price=100.0, exit_price=110.0, quantity=10)
    config = SlippageConfig(entry_slippage_percent=1.0, exit_slippage_percent=1.0)

    adjusted = slippage.apply([trade], config)[0]

    expected_pnl = round((adjusted.exit_price - adjusted.entry_price) * 10, 4)
    assert adjusted.pnl == expected_pnl


def test_slippage_always_reduces_long_profit() -> None:
    trade = make_trade(entry_price=100.0, exit_price=110.0, quantity=10)
    config = SlippageConfig(entry_slippage_percent=0.5, exit_slippage_percent=0.5)

    adjusted = slippage.apply([trade], config)[0]

    assert adjusted.pnl < trade.pnl


def test_zero_slippage_leaves_pnl_unchanged() -> None:
    trade = make_trade(entry_price=100.0, exit_price=110.0, quantity=10)
    config = SlippageConfig(entry_slippage_percent=0.0, exit_slippage_percent=0.0)

    adjusted = slippage.apply([trade], config)[0]

    assert adjusted.pnl == trade.pnl


def test_rejects_negative_slippage() -> None:
    with pytest.raises(ValidationError):
        SlippageConfig(entry_slippage_percent=-1.0, exit_slippage_percent=0.0)
