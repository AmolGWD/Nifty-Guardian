#!/usr/bin/env python3
"""
Standalone demonstration of the Grid Search Strategy Optimization
Engine (Phase 16).

Uses a deliberately small search space (3 EMA periods x 2 RSI bullish
thresholds x 2 reward/risk ratios = 12 combinations) against the
existing sample dataset, prints every combination's parameters and
weighted score, then the best configuration and a top-5 ranking.

Requires no Zerodha credentials, no network access, and no FastAPI
server. Run from anywhere:

    python3 scripts/demo_grid_search.py
"""

from __future__ import annotations

import sys
from pathlib import Path

_BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

from app.optimization.optimizer import optimize  # noqa: E402
from app.optimization.parameter_space import (  # noqa: E402
    OptimizableParameter,
    ParameterSpace,
    ParameterType,
)
from app.optimization.report import render_markdown  # noqa: E402
from app.trading.backtest.models import BacktestConfig  # noqa: E402
from app.trading.risk.models import RiskConfig  # noqa: E402

SAMPLE_CSV = _BACKEND_DIR / "app" / "market_data" / "sample_data" / "nifty_sample_candles.csv"


def _print_header(title: str) -> None:
    banner = "=" * 70
    print(f"\n{banner}\n{title}\n{banner}")


def build_small_search_space() -> ParameterSpace:
    ema_period = OptimizableParameter(
        name="ema_period",
        description="Candle period used to compute the EMA indicator value.",
        parameter_type=ParameterType.INT,
        minimum=14,
        maximum=18,
        step=2,
        default=16,
        safe_to_optimize=True,
    )
    rsi_bullish_threshold = OptimizableParameter(
        name="rsi_bullish_threshold",
        description="RSI value above which the RSI confirmation check reports Long.",
        parameter_type=ParameterType.FLOAT,
        minimum=50,
        maximum=55,
        step=5,
        default=55,
        safe_to_optimize=True,
    )
    reward_risk_ratio = OptimizableParameter(
        name="reward_risk_ratio",
        description="Target distance / stop-loss distance.",
        parameter_type=ParameterType.FLOAT,
        minimum=2.0,
        maximum=2.5,
        step=0.5,
        default=2.0,
        safe_to_optimize=True,
    )
    return ParameterSpace(parameters=(ema_period, rsi_bullish_threshold, reward_risk_ratio))


def main() -> None:
    space = build_small_search_space()
    _print_header("SEARCH SPACE")
    print(f"Total combinations: {space.total_combinations()}")
    for parameter in space.parameters:
        print(f"  {parameter.name}: {parameter.values()}")

    base_config = BacktestConfig(initial_capital=100_000.0, risk_config=RiskConfig())

    _print_header("RUNNING GRID SEARCH")
    run, ranked, report = optimize(
        parameter_space=space,
        dataset_path=str(SAMPLE_CSV),
        base_backtest_config=base_config,
    )
    print(f"Completed {run.total_combinations - run.failed_count}/{run.total_combinations} "
          f"combinations ({run.failed_count} failed) in {run.duration_seconds:.3f}s")

    _print_header("EVERY COMBINATION AND ITS WEIGHTED SCORE")
    for ranked_result in ranked:
        result = ranked_result.result
        score = f"{ranked_result.score:.4f}" if ranked_result.score is not None else "N/A"
        print(f"  {result.combination_id} {result.parameter_values} -> score={score}")

    _print_header("BEST CONFIGURATION")
    best = ranked[0]
    print(f"Rank 1: {best.result.combination_id}")
    print(f"Parameters: {best.result.parameter_values}")
    print(f"Weighted score: {best.score:.4f}" if best.score is not None else "Weighted score: N/A")
    backtest_result = best.result.experiment_result.backtest_result
    if backtest_result is not None:
        print(f"Net profit: {backtest_result.report.net_profit:.4f}")
        print(f"Total trades: {backtest_result.report.total_trades}")

    _print_header("TOP 5 RANKING")
    for ranked_result in ranked[:5]:
        score = f"{ranked_result.score:.4f}" if ranked_result.score is not None else "N/A"
        print(
            f"  #{ranked_result.rank} {ranked_result.result.combination_id} "
            f"{ranked_result.result.parameter_values} -> {score}"
        )

    _print_header("FULL REPORT (MARKDOWN)")
    print(render_markdown(report))


if __name__ == "__main__":
    main()
