#!/usr/bin/env python3
"""
Standalone demonstration of the Strategy Experiment Framework.

Creates three experiments against the existing sample dataset, each
with a different risk configuration (the framework does not
understand or vary strategy-internal parameters like EMA period or
RSI threshold - those aren't wired into anything yet; Strategy
Optimization, not this phase, will give them something real to
drive). Runs them through the existing (frozen) Backtest and Analytics
Engines, compares and ranks them, exports the results in all three
formats, and prints a comparison table.

Requires no Zerodha credentials, no network access, and no FastAPI
server. Run from anywhere:

    python3 scripts/demo_experiment_framework.py
"""

from __future__ import annotations

import sys
from pathlib import Path

_BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

from app.research.comparison import ExperimentComparison, compare_experiments  # noqa: E402
from app.research.experiment import create_experiment  # noqa: E402
from app.research.experiment_registry import ExperimentRegistry  # noqa: E402
from app.research.experiment_runner import run_experiments  # noqa: E402
from app.research.export import export_csv, export_json, export_markdown  # noqa: E402
from app.research.models import Metric  # noqa: E402
from app.research.ranking import rank_experiments  # noqa: E402
from app.research.scoring import ScoringWeights, calculate_scores  # noqa: E402
from app.trading.backtest.models import BacktestConfig  # noqa: E402
from app.trading.risk.models import RiskConfig  # noqa: E402

SAMPLE_CSV = _BACKEND_DIR / "app" / "market_data" / "sample_data" / "nifty_sample_candles.csv"
EXPORT_DIR = Path(__file__).resolve().parent / "sample_data"


def _print_header(title: str) -> None:
    banner = "=" * 33
    print(f"\n{banner}")
    print(title)
    print(banner)


def _comparisons_by_id(
    comparisons: list[ExperimentComparison],
) -> dict[str, ExperimentComparison]:
    return {comparison.experiment_id: comparison for comparison in comparisons}


def _build_config(
    *, risk_per_trade_percent: float, stop_loss_atr_multiplier: float
) -> BacktestConfig:
    return BacktestConfig(
        initial_capital=100_000.0,
        risk_config=RiskConfig(
            risk_per_trade_percent=risk_per_trade_percent,
            stop_loss_atr_multiplier=stop_loss_atr_multiplier,
            target_atr_multiplier=3.0,
            max_daily_loss=5_000.0,
            max_trades_per_day=5,
            max_concurrent_positions=1,
            max_capital_exposure_percent=100.0,
        ),
    )


def main() -> None:
    registry = ExperimentRegistry()

    _print_header("CREATE EXPERIMENTS")
    experiments = [
        create_experiment(
            name="Conservative",
            description="Low risk-per-trade, tight stop",
            strategy="EMABreakout",
            dataset_path=str(SAMPLE_CSV),
            backtest_config=_build_config(
                risk_per_trade_percent=0.5, stop_loss_atr_multiplier=1.0
            ),
            parameters={"risk_percent": 0.5, "stop_loss_atr_multiplier": 1.0},
            tags=["baseline", "conservative"],
            notes="Baseline low-risk configuration",
        ),
        create_experiment(
            name="Balanced",
            description="Default risk-per-trade and stop distance",
            strategy="EMABreakout",
            dataset_path=str(SAMPLE_CSV),
            backtest_config=_build_config(
                risk_per_trade_percent=1.0, stop_loss_atr_multiplier=1.5
            ),
            parameters={"risk_percent": 1.0, "stop_loss_atr_multiplier": 1.5},
            tags=["baseline", "balanced"],
            notes="Baseline balanced configuration",
        ),
        create_experiment(
            name="Aggressive",
            description="Higher risk-per-trade, wider stop",
            strategy="EMABreakout",
            dataset_path=str(SAMPLE_CSV),
            backtest_config=_build_config(
                risk_per_trade_percent=2.0, stop_loss_atr_multiplier=2.0
            ),
            parameters={"risk_percent": 2.0, "stop_loss_atr_multiplier": 2.0},
            tags=["baseline", "aggressive"],
            notes="Baseline higher-risk configuration",
        ),
    ]
    for experiment in experiments:
        registry.register(experiment)
        print(f"  {experiment.name} ({experiment.experiment_id})")

    _print_header("RUN EXPERIMENTS")
    results = run_experiments(experiments)
    for result in results:
        registry.record_result(result)
        print(f"  {result.experiment.name}: {result.status.value} ({result.duration_seconds:.3f}s)")

    _print_header("COMPARE EXPERIMENTS")
    metrics = [
        Metric.NET_PROFIT,
        Metric.PROFIT_FACTOR,
        Metric.EXPECTANCY,
        Metric.MAX_DRAWDOWN,
        Metric.SHARPE_RATIO,
    ]
    comparisons = compare_experiments(results, metrics)
    header = "Name".ljust(14) + "".join(metric.value.ljust(16) for metric in metrics)
    print(header)
    for comparison in comparisons:
        row = comparison.name.ljust(14)
        for metric in metrics:
            value = comparison.metrics[metric]
            row += (f"{value:.2f}" if value is not None else "N/A").ljust(16)
        print(row)

    _print_header("RANK EXPERIMENTS (by Net Profit)")
    ranked = rank_experiments(results, Metric.NET_PROFIT)
    comparisons_lookup = _comparisons_by_id(comparisons)
    for position, result in enumerate(ranked, start=1):
        net_profit = comparisons_lookup[result.experiment.experiment_id].metrics[
            Metric.NET_PROFIT
        ]
        print(f"  #{position} {result.experiment.name}: {net_profit}")

    _print_header("WEIGHTED SCORING")
    weights = ScoringWeights(
        weights={
            Metric.PROFIT_FACTOR: 0.30,
            Metric.MAX_DRAWDOWN: 0.25,
            Metric.EXPECTANCY: 0.20,
            Metric.RECOVERY_FACTOR: 0.15,
            Metric.WIN_RATE: 0.10,
        }
    )
    scores = calculate_scores(results, weights)
    for result in results:
        score = scores[result.experiment.experiment_id]
        print(f"  {result.experiment.name}: {score:.4f}")

    _print_header("EXPORT RESULTS")
    json_path = EXPORT_DIR / "experiment_results.json"
    csv_path = EXPORT_DIR / "experiment_results.csv"
    markdown_path = EXPORT_DIR / "experiment_results.md"
    export_json(results, json_path, ranking=ranked)
    export_csv(results, csv_path, ranking=ranked)
    export_markdown(results, markdown_path, ranking=ranked)
    print(f"  JSON:     {json_path}")
    print(f"  CSV:      {csv_path}")
    print(f"  Markdown: {markdown_path}")


if __name__ == "__main__":
    main()
