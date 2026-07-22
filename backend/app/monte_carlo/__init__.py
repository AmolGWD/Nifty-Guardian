"""
Monte Carlo Analysis Framework (Phase 18).

Evaluates strategy robustness under realistic execution uncertainty by
perturbing an already-completed backtest's trade outcomes (trade
order, slippage, commission, execution delay, missed trades, position
sizing) many times and measuring the resulting distribution. Does not
optimize and does not change trading logic. See
`docs/MONTE_CARLO_GUIDE.md` for the full guide.
"""

from app.monte_carlo.models import MonteCarloRun, PerturbationConfig, SimulationResult
from app.monte_carlo.perturbations.commission import CommissionConfig
from app.monte_carlo.perturbations.execution_delay import ExecutionDelayConfig
from app.monte_carlo.perturbations.missed_trade import MissedTradeConfig
from app.monte_carlo.perturbations.position_variation import PositionVariationConfig
from app.monte_carlo.perturbations.slippage import SlippageConfig
from app.monte_carlo.report import MonteCarloReport, build_report
from app.monte_carlo.runner import run_monte_carlo_simulation
from app.monte_carlo.statistics import ConfidenceInterval, MonteCarloStatistics, compute_statistics

__all__ = [
    "CommissionConfig",
    "ConfidenceInterval",
    "ExecutionDelayConfig",
    "MissedTradeConfig",
    "MonteCarloReport",
    "MonteCarloRun",
    "MonteCarloStatistics",
    "PerturbationConfig",
    "PositionVariationConfig",
    "SimulationResult",
    "SlippageConfig",
    "build_report",
    "compute_statistics",
    "run_monte_carlo_simulation",
]
