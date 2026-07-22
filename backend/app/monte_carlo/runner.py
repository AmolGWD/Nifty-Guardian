"""
Runs N Monte Carlo simulations against one already-completed
`BacktestResult`, using a single seeded `random.Random` stream shared
across all simulations - the same seed always reproduces the exact
same sequence of `num_simulations` results.

Parallel-ready, serial today: `simulation.run_one_simulation()` is a
pure function of `(trades, config, an rng, candles)` with no shared
mutable state except the rng itself - splitting this loop across
worker processes would only require giving each worker its own
independently-seeded `random.Random(seed + worker_offset)` instead of
one continuous stream. Not implemented, since the CTO brief accepts a
serial implementation - this describes what would need to change, not
a promise of a future phase.
"""

import random
import time
import uuid
from datetime import datetime

from app.market_data.schemas import Candle
from app.monte_carlo.models import MonteCarloRun, PerturbationConfig, SimulationResult
from app.monte_carlo.simulation import run_one_simulation
from app.trading.backtest.models import BacktestResult


def run_monte_carlo_simulation(
    *,
    backtest_result: BacktestResult,
    perturbation_config: PerturbationConfig,
    num_simulations: int,
    seed: int,
    candles: list[Candle] | None = None,
) -> MonteCarloRun:
    if num_simulations <= 0:
        raise ValueError("num_simulations must be positive")

    rng = random.Random(seed)
    start = time.perf_counter()

    results: list[SimulationResult] = []
    for index in range(num_simulations):
        results.append(
            run_one_simulation(
                backtest_result.trades,
                initial_capital=backtest_result.config.initial_capital,
                perturbation_config=perturbation_config,
                rng=rng,
                candles=candles,
                simulation_index=index,
            )
        )

    return MonteCarloRun(
        run_id=str(uuid.uuid4()),
        created_date=datetime.now(),
        seed=seed,
        num_simulations=num_simulations,
        perturbation_config=perturbation_config,
        initial_capital=backtest_result.config.initial_capital,
        baseline_net_profit=backtest_result.report.net_profit,
        baseline_max_drawdown=backtest_result.report.max_drawdown,
        results=tuple(results),
        duration_seconds=time.perf_counter() - start,
    )
