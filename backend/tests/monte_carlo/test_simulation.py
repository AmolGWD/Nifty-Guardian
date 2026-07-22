import random

import pytest

from app.monte_carlo.models import PerturbationConfig
from app.monte_carlo.perturbations.commission import CommissionConfig
from app.monte_carlo.perturbations.execution_delay import ExecutionDelayConfig
from app.monte_carlo.perturbations.missed_trade import MissedTradeConfig
from app.monte_carlo.simulation import run_one_simulation
from tests.monte_carlo.helpers import make_trade


def test_no_perturbations_reproduces_the_original_outcome() -> None:
    trades = [
        make_trade(entry_price=100.0, exit_price=110.0, quantity=10),
        make_trade(entry_price=110.0, exit_price=105.0, quantity=10),
    ]

    result = run_one_simulation(
        trades,
        initial_capital=100_000.0,
        perturbation_config=PerturbationConfig(),
        rng=random.Random(1),
        candles=None,
    )

    expected_net_profit = sum(trade.pnl for trade in trades)
    assert result.net_profit == pytest.approx(expected_net_profit)
    assert result.total_trades == 2


def test_missed_trades_can_reduce_total_trade_count() -> None:
    trades = [make_trade(entry_price=100.0 + i) for i in range(50)]

    result = run_one_simulation(
        trades,
        initial_capital=100_000.0,
        perturbation_config=PerturbationConfig(
            missed_trades=MissedTradeConfig(miss_probability_percent=50.0)
        ),
        rng=random.Random(1),
        candles=None,
    )

    assert result.total_trades < 50


def test_commission_reduces_net_profit() -> None:
    trades = [make_trade(entry_price=100.0, exit_price=110.0, quantity=10)]

    baseline = run_one_simulation(
        trades, initial_capital=100_000.0, perturbation_config=PerturbationConfig(),
        rng=random.Random(1), candles=None,
    )
    with_commission = run_one_simulation(
        trades, initial_capital=100_000.0,
        perturbation_config=PerturbationConfig(
            commission=CommissionConfig(flat_commission_per_trade=10.0)
        ),
        rng=random.Random(1), candles=None,
    )

    assert with_commission.net_profit < baseline.net_profit


def test_execution_delay_without_candles_raises() -> None:
    trades = [make_trade()]

    with pytest.raises(ValueError, match="execution_delay"):
        run_one_simulation(
            trades, initial_capital=100_000.0,
            perturbation_config=PerturbationConfig(
                execution_delay=ExecutionDelayConfig(delay_candles=1)
            ),
            rng=random.Random(1), candles=None,
        )


def test_empty_trade_list_produces_zero_profit_result() -> None:
    result = run_one_simulation(
        [], initial_capital=100_000.0, perturbation_config=PerturbationConfig(),
        rng=random.Random(1), candles=None,
    )

    assert result.total_trades == 0
    assert result.net_profit == 0.0
    assert result.final_capital == 100_000.0


def test_max_drawdown_is_zero_for_all_winning_trades() -> None:
    trades = [make_trade(entry_price=100.0, exit_price=110.0) for _ in range(5)]

    result = run_one_simulation(
        trades, initial_capital=100_000.0, perturbation_config=PerturbationConfig(),
        rng=random.Random(1), candles=None,
    )

    assert result.max_drawdown == 0.0


def test_max_drawdown_is_positive_when_equity_dips() -> None:
    trades = [
        make_trade(entry_price=100.0, exit_price=110.0, quantity=10),  # +100
        make_trade(entry_price=100.0, exit_price=80.0, quantity=10),  # -200
    ]

    result = run_one_simulation(
        trades, initial_capital=100_000.0, perturbation_config=PerturbationConfig(),
        rng=random.Random(1), candles=None,
    )

    assert result.max_drawdown == pytest.approx(200.0)


def test_simulation_index_is_recorded() -> None:
    result = run_one_simulation(
        [make_trade()], initial_capital=100_000.0, perturbation_config=PerturbationConfig(),
        rng=random.Random(1), candles=None, simulation_index=7,
    )

    assert result.simulation_index == 7
