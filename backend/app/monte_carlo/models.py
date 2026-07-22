"""
Monte Carlo Analysis Framework domain models.

Every model here is a frozen Pydantic model (ADR-0006). This package
does not optimize and does not change trading logic - it perturbs an
already-completed backtest's trade outcomes (`BacktestResult.trades`)
many times and measures how the resulting distribution of outcomes
behaves, reusing `app.trading.backtest.performance.calculate_max_drawdown`
for the one piece of arithmetic that already exists rather than
duplicating it (see `simulation.py`).
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, model_validator

from app.config.validation import ParameterValidationError
from app.monte_carlo.perturbations.commission import CommissionConfig
from app.monte_carlo.perturbations.execution_delay import ExecutionDelayConfig
from app.monte_carlo.perturbations.missed_trade import MissedTradeConfig
from app.monte_carlo.perturbations.position_variation import PositionVariationConfig
from app.monte_carlo.perturbations.slippage import SlippageConfig


class PerturbationConfig(BaseModel):
    """
    Which perturbations to apply, and their settings. Every field
    defaults to "off" (`False`/`None`) - a `PerturbationConfig()` with
    no arguments perturbs nothing, so a simulation run with it just
    re-measures the exact original trade sequence `num_simulations`
    times (a useful sanity check, not a meaningful Monte Carlo run on
    its own).
    """

    model_config = ConfigDict(frozen=True)

    trade_shuffle_enabled: bool = False
    slippage: SlippageConfig | None = None
    commission: CommissionConfig | None = None
    execution_delay: ExecutionDelayConfig | None = None
    missed_trades: MissedTradeConfig | None = None
    position_variation: PositionVariationConfig | None = None

    def enabled_names(self) -> tuple[str, ...]:
        names = []
        if self.trade_shuffle_enabled:
            names.append("TradeShuffle")
        if self.slippage is not None:
            names.append("Slippage")
        if self.commission is not None:
            names.append("Commission")
        if self.execution_delay is not None:
            names.append("ExecutionDelay")
        if self.missed_trades is not None:
            names.append("MissedTrades")
        if self.position_variation is not None:
            names.append("PositionVariation")
        return tuple(names)


class SimulationResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    simulation_index: int
    final_capital: float
    net_profit: float
    total_return_percent: float
    max_drawdown: float
    total_trades: int


class MonteCarloRun(BaseModel):
    model_config = ConfigDict(frozen=True)

    run_id: str
    created_date: datetime
    seed: int
    num_simulations: int
    perturbation_config: PerturbationConfig
    initial_capital: float
    baseline_net_profit: float
    baseline_max_drawdown: float
    results: tuple[SimulationResult, ...]
    duration_seconds: float

    @model_validator(mode="after")
    def _validate(self) -> "MonteCarloRun":
        if self.num_simulations <= 0:
            raise ParameterValidationError("num_simulations must be positive")
        return self
