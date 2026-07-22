import random

import pytest
from pydantic import ValidationError

from app.monte_carlo.perturbations import missed_trade
from app.monte_carlo.perturbations.missed_trade import MissedTradeConfig
from tests.monte_carlo.helpers import make_trade


def test_zero_percent_never_drops_a_trade() -> None:
    trades = [make_trade(entry_price=100.0 + i) for i in range(50)]
    config = MissedTradeConfig(miss_probability_percent=0.0)

    result = missed_trade.apply(trades, config, random.Random(1))

    assert len(result) == len(trades)


def test_hundred_percent_drops_every_trade() -> None:
    trades = [make_trade(entry_price=100.0 + i) for i in range(50)]
    config = MissedTradeConfig(miss_probability_percent=100.0)

    result = missed_trade.apply(trades, config, random.Random(1))

    assert result == []


def test_remaining_trades_are_unmodified() -> None:
    trades = [make_trade(entry_price=100.0 + i) for i in range(50)]
    config = MissedTradeConfig(miss_probability_percent=50.0)

    result = missed_trade.apply(trades, config, random.Random(1))

    assert all(trade in trades for trade in result)


def test_same_seed_drops_the_same_trades() -> None:
    trades = [make_trade(entry_price=100.0 + i) for i in range(50)]
    config = MissedTradeConfig(miss_probability_percent=30.0)

    first = missed_trade.apply(trades, config, random.Random(7))
    second = missed_trade.apply(trades, config, random.Random(7))

    assert first == second


def test_rejects_out_of_range_probability() -> None:
    with pytest.raises(ValidationError):
        MissedTradeConfig(miss_probability_percent=150.0)
