import random

import pytest
from pydantic import ValidationError

from app.monte_carlo.perturbations import position_variation
from app.monte_carlo.perturbations.position_variation import PositionVariationConfig
from tests.monte_carlo.helpers import make_trade


def test_quantity_varies_within_configured_bounds() -> None:
    trade = make_trade(entry_price=100.0, exit_price=110.0, quantity=100)
    config = PositionVariationConfig(min_variation_percent=-20.0, max_variation_percent=20.0)
    rng = random.Random(1)

    for _ in range(50):
        adjusted = position_variation.apply([trade], config, rng)[0]
        assert 80 <= adjusted.quantity <= 120


def test_quantity_never_drops_below_one() -> None:
    trade = make_trade(entry_price=100.0, exit_price=110.0, quantity=1)
    config = PositionVariationConfig(min_variation_percent=-99.0, max_variation_percent=-90.0)

    adjusted = position_variation.apply([trade], config, random.Random(1))[0]

    assert adjusted.quantity >= 1


def test_pnl_is_recomputed_from_new_quantity() -> None:
    trade = make_trade(entry_price=100.0, exit_price=110.0, quantity=100)
    config = PositionVariationConfig(min_variation_percent=-0.001, max_variation_percent=0.001)

    adjusted = position_variation.apply([trade], config, random.Random(1))[0]

    assert adjusted.quantity == 100
    assert adjusted.pnl == trade.pnl


def test_prices_are_unchanged() -> None:
    trade = make_trade(entry_price=100.0, exit_price=110.0, quantity=100)
    config = PositionVariationConfig(min_variation_percent=-20.0, max_variation_percent=20.0)

    adjusted = position_variation.apply([trade], config, random.Random(1))[0]

    assert adjusted.entry_price == trade.entry_price
    assert adjusted.exit_price == trade.exit_price


def test_same_seed_produces_same_variation() -> None:
    trade = make_trade(entry_price=100.0, exit_price=110.0, quantity=100)
    config = PositionVariationConfig(min_variation_percent=-20.0, max_variation_percent=20.0)

    first = position_variation.apply([trade], config, random.Random(9))
    second = position_variation.apply([trade], config, random.Random(9))

    assert first == second


def test_rejects_min_not_less_than_max() -> None:
    with pytest.raises(ValidationError):
        PositionVariationConfig(min_variation_percent=10.0, max_variation_percent=10.0)


def test_rejects_min_at_or_below_negative_100() -> None:
    with pytest.raises(ValidationError):
        PositionVariationConfig(min_variation_percent=-100.0, max_variation_percent=0.0)
