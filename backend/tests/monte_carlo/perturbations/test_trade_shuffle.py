import random

from app.monte_carlo.perturbations import trade_shuffle
from tests.monte_carlo.helpers import make_trade


def test_preserves_the_same_set_of_trades() -> None:
    trades = [make_trade(entry_price=100.0 + i) for i in range(5)]

    shuffled = trade_shuffle.apply(trades, random.Random(1))

    assert sorted(shuffled, key=lambda t: t.entry_price) == sorted(
        trades, key=lambda t: t.entry_price
    )
    assert len(shuffled) == len(trades)


def test_does_not_mutate_individual_trades() -> None:
    trades = [make_trade(entry_price=100.0 + i) for i in range(3)]

    shuffled = trade_shuffle.apply(trades, random.Random(1))

    assert {id(t) for t in shuffled} == {id(t) for t in trades}


def test_same_seed_produces_same_order() -> None:
    trades = [make_trade(entry_price=100.0 + i) for i in range(10)]

    first = trade_shuffle.apply(trades, random.Random(42))
    second = trade_shuffle.apply(trades, random.Random(42))

    assert first == second


def test_different_seeds_can_produce_different_order() -> None:
    trades = [make_trade(entry_price=100.0 + i) for i in range(10)]

    first = trade_shuffle.apply(trades, random.Random(1))
    second = trade_shuffle.apply(trades, random.Random(2))

    assert first != second


def test_original_list_is_not_mutated() -> None:
    trades = [make_trade(entry_price=100.0 + i) for i in range(5)]
    original_order = list(trades)

    trade_shuffle.apply(trades, random.Random(1))

    assert trades == original_order
