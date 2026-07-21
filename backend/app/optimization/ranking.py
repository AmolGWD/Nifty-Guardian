"""
Ranks OptimizationResults - by a single Metric (delegating entirely to
`app.research.ranking.rank_experiments()`/`app.research.models.
extract_metric()`) or by a weighted score across several metrics
(delegating to `app.research.scoring.calculate_scores()`). No ranking
logic is duplicated here - this module only maps `OptimizationResult`
to/from the underlying `ExperimentResult` the research package already
knows how to rank.

`RankBy` is this package's own enum, not `app.research.models.Metric`
itself - `Metric` has no "weighted score" concept (scoring and ranking
are deliberately separate in `app.research`), and this package's
default ranking mode is the weighted score, per the CTO brief.
"""

from enum import StrEnum

from app.optimization.models import OptimizationResult, RankedOptimizationResult
from app.research.models import ExperimentResult, Metric, extract_metric
from app.research.ranking import rank_experiments
from app.research.scoring import ScoringWeights, calculate_scores


class RankBy(StrEnum):
    WEIGHTED_SCORE = "WeightedScore"
    PROFIT_FACTOR = "ProfitFactor"
    NET_PROFIT = "NetProfit"
    SHARPE_RATIO = "SharpeRatio"
    RECOVERY_FACTOR = "RecoveryFactor"
    MAX_DRAWDOWN = "MaxDrawdown"
    WIN_RATE = "WinRate"


_RANK_BY_TO_METRIC: dict[RankBy, Metric] = {
    RankBy.PROFIT_FACTOR: Metric.PROFIT_FACTOR,
    RankBy.NET_PROFIT: Metric.NET_PROFIT,
    RankBy.SHARPE_RATIO: Metric.SHARPE_RATIO,
    RankBy.RECOVERY_FACTOR: Metric.RECOVERY_FACTOR,
    RankBy.MAX_DRAWDOWN: Metric.MAX_DRAWDOWN,
    RankBy.WIN_RATE: Metric.WIN_RATE,
}

# A reasonable, documented default weighting (see docs/OPTIMIZATION_GUIDE.md)
# - not the only valid choice, callers may supply their own ScoringWeights.
DEFAULT_SCORING_WEIGHTS = ScoringWeights(
    weights={
        Metric.PROFIT_FACTOR: 0.3,
        Metric.SHARPE_RATIO: 0.3,
        Metric.RECOVERY_FACTOR: 0.2,
        Metric.WIN_RATE: 0.2,
    }
)


def rank_optimization_results(
    results: list[OptimizationResult],
    *,
    rank_by: RankBy = RankBy.WEIGHTED_SCORE,
    weights: ScoringWeights | None = None,
) -> list[RankedOptimizationResult]:
    by_experiment_id = {
        result.experiment_result.experiment.experiment_id: result for result in results
    }
    experiment_results = [result.experiment_result for result in results]

    if rank_by == RankBy.WEIGHTED_SCORE:
        scores = calculate_scores(experiment_results, weights or DEFAULT_SCORING_WEIGHTS)
        ordered_ids = sorted(scores, key=lambda experiment_id: scores[experiment_id], reverse=True)
        return [
            RankedOptimizationResult(
                result=by_experiment_id[experiment_id], rank=rank, score=scores[experiment_id]
            )
            for rank, experiment_id in enumerate(ordered_ids, start=1)
        ]

    metric = _RANK_BY_TO_METRIC[rank_by]
    ranked_experiment_results = rank_experiments(experiment_results, metric)
    return [
        RankedOptimizationResult(
            result=by_experiment_id[_experiment_id(experiment_result)],
            rank=rank,
            score=extract_metric(experiment_result, metric),
        )
        for rank, experiment_result in enumerate(ranked_experiment_results, start=1)
    ]


def _experiment_id(experiment_result: ExperimentResult) -> str:
    return experiment_result.experiment.experiment_id
