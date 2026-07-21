"""
Public entry point tying the rest of this package together: generate
the grid, execute it, rank the results, and build the report - the
one function most callers (scripts, tests) need.
"""

from app.optimization.executor import run_grid_search
from app.optimization.models import OptimizationReport, OptimizationRun, RankedOptimizationResult
from app.optimization.parameter_space import ParameterSpace
from app.optimization.ranking import RankBy, rank_optimization_results
from app.optimization.report import build_optimization_report
from app.research.scoring import ScoringWeights
from app.trading.backtest.models import BacktestConfig


def optimize(
    *,
    parameter_space: ParameterSpace,
    dataset_path: str,
    base_backtest_config: BacktestConfig,
    strategy_name: str = "EMABreakout",
    rank_by: RankBy = RankBy.WEIGHTED_SCORE,
    weights: ScoringWeights | None = None,
) -> tuple[OptimizationRun, list[RankedOptimizationResult], OptimizationReport]:
    run = run_grid_search(
        parameter_space=parameter_space,
        dataset_path=dataset_path,
        base_backtest_config=base_backtest_config,
        strategy_name=strategy_name,
    )
    ranked = rank_optimization_results(list(run.results), rank_by=rank_by, weights=weights)
    report = build_optimization_report(run, rank_by=rank_by, weights=weights)

    return run, ranked, report
