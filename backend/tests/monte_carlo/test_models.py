from datetime import datetime

import pytest
from pydantic import ValidationError

from app.monte_carlo.models import MonteCarloRun, PerturbationConfig
from app.monte_carlo.perturbations.missed_trade import MissedTradeConfig
from app.monte_carlo.perturbations.slippage import SlippageConfig


def test_default_perturbation_config_has_nothing_enabled() -> None:
    config = PerturbationConfig()

    assert config.enabled_names() == ()


def test_enabled_names_reflects_configured_perturbations() -> None:
    config = PerturbationConfig(
        trade_shuffle_enabled=True,
        slippage=SlippageConfig(entry_slippage_percent=0.1, exit_slippage_percent=0.1),
        missed_trades=MissedTradeConfig(miss_probability_percent=1.0),
    )

    assert config.enabled_names() == ("TradeShuffle", "Slippage", "MissedTrades")


def test_perturbation_config_is_immutable() -> None:
    config = PerturbationConfig()

    with pytest.raises(ValidationError):
        config.trade_shuffle_enabled = True  # type: ignore[misc]


def _valid_run_kwargs(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = dict(
        run_id="run-1",
        created_date=datetime(2026, 1, 1),
        seed=1,
        num_simulations=10,
        perturbation_config=PerturbationConfig(),
        initial_capital=100_000.0,
        baseline_net_profit=1000.0,
        baseline_max_drawdown=100.0,
        results=(),
        duration_seconds=1.0,
    )
    base.update(overrides)
    return base


def test_monte_carlo_run_rejects_non_positive_num_simulations() -> None:
    with pytest.raises(ValidationError, match="num_simulations"):
        MonteCarloRun(**_valid_run_kwargs(num_simulations=0))


def test_monte_carlo_run_is_immutable() -> None:
    run = MonteCarloRun(**_valid_run_kwargs())

    with pytest.raises(ValidationError):
        run.seed = 99  # type: ignore[misc]
