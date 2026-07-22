#!/usr/bin/env python3
"""
Standalone demonstration of the Walk-Forward Validation Framework
(Phase 17).

Generates a small synthetic dataset (consecutive trading weekdays,
weekends skipped - session validation rejects them), runs Rolling-
window validation with a deliberately small search space (a single
risk_percent dimension), prints every window's train/test comparison,
and reports the overall robustness score.

Requires no Zerodha credentials, no network access, and no FastAPI
server. Run from anywhere:

    python3 scripts/demo_walk_forward.py
"""

from __future__ import annotations

import csv
import sys
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

_BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

from app.market_data.schemas import Candle  # noqa: E402
from app.optimization.parameter_space import (  # noqa: E402
    OptimizableParameter,
    ParameterSpace,
    ParameterType,
)
from app.trading.backtest.models import BacktestConfig  # noqa: E402
from app.trading.risk.models import RiskConfig  # noqa: E402
from app.validation.models import ValidationRules, WindowConfig, WindowStatus, WindowType  # noqa: E402
from app.validation.report import build_validation_report, render_markdown  # noqa: E402
from app.validation.runner import run_walk_forward_validation  # noqa: E402


def _print_header(title: str) -> None:
    banner = "=" * 70
    print(f"\n{banner}\n{title}\n{banner}")


def build_weekday_candles(num_days: int, start: datetime) -> list[Candle]:
    """Consecutive weekdays only, a clear uptrend each day (see docs/VALIDATION_GUIDE.md)."""
    candles: list[Candle] = []
    close = 100.0
    day = start

    while len(candles) < num_days * 25:
        if day.isoweekday() in (6, 7):
            day += timedelta(days=1)
            continue

        timestamp = day
        for i in range(25):
            open_price = close
            close = close - 1.0 if i % 6 == 5 else close + 2.5
            high = max(open_price, close) + 1.0
            low = min(open_price, close) - 1.0
            volume = 10_000 + (i * 500)
            candles.append(
                Candle(
                    timestamp=timestamp, open=open_price, high=high, low=low, close=close,
                    volume=volume,
                )
            )
            timestamp += timedelta(minutes=15)
        day += timedelta(days=1)

    return candles


def write_candles_csv(candles: list[Candle], path: Path) -> None:
    with open(path, "w", newline="", encoding="utf-8") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(["Timestamp", "Open", "High", "Low", "Close", "Volume"])
        for candle in candles:
            writer.writerow(
                [
                    candle.timestamp.isoformat(), candle.open, candle.high, candle.low,
                    candle.close, candle.volume,
                ]
            )


def main() -> None:
    _print_header("1. Generate synthetic dataset")
    candles = build_weekday_candles(20, start=datetime(2026, 1, 5, 9, 15))  # a Monday
    dataset_path = Path(tempfile.mkdtemp(prefix="demo-walk-forward-")) / "synthetic.csv"
    write_candles_csv(candles, dataset_path)
    print(f"{len(candles)} candles, {candles[0].timestamp} -> {candles[-1].timestamp}")

    window_config = WindowConfig(
        window_type=WindowType.ROLLING,
        training_duration_days=8,
        testing_duration_days=4,
        step_size_days=4,
        minimum_candles=20,
        minimum_trades=0,
    )
    space = ParameterSpace(
        parameters=(
            OptimizableParameter(
                name="risk_percent", description="Percent of capital risked per trade",
                parameter_type=ParameterType.FLOAT, minimum=0.5, maximum=1.5, step=0.5,
                default=1.0, safe_to_optimize=True,
            ),
        )
    )
    rules = ValidationRules(
        max_drawdown_increase_percent=100.0,
        min_profit_factor=0.0,
        max_performance_degradation_percent=100.0,
        min_trade_count=0,
        min_robustness_score_percent=50.0,
    )
    base_config = BacktestConfig(initial_capital=100_000.0, risk_config=RiskConfig(), warmup_candles=20)

    _print_header("2. Generate windows, optimize each, validate each")
    print(f"Window type: {window_config.window_type.value}")
    print(f"Training duration: {window_config.training_duration_days} days")
    print(f"Testing duration: {window_config.testing_duration_days} days")
    print(f"Search space: {space.dimension_names()}")

    run = run_walk_forward_validation(
        window_config=window_config,
        parameter_space=space,
        validation_rules=rules,
        dataset_path=str(dataset_path),
        base_backtest_config=base_config,
    )
    print(f"\nGenerated {len(run.results)} windows in {run.duration_seconds:.3f}s")

    _print_header("3. Print summary table")
    print(f"{'#':<4}{'Status':<18}{'Train Net Profit':<18}{'Test Net Profit':<18}{'Pass':<6}")
    for result in run.results:
        train_profit = "N/A"
        test_profit = "N/A"
        passed = "N/A"
        if result.train_result and result.train_result.backtest_result:
            train_profit = f"{result.train_result.backtest_result.report.net_profit:.2f}"
        if result.test_result and result.test_result.backtest_result:
            test_profit = f"{result.test_result.backtest_result.report.net_profit:.2f}"
        if result.pass_fail:
            passed = str(result.pass_fail.passed)
        print(
            f"{result.window.window_index:<4}{result.status.value:<18}"
            f"{train_profit:<18}{test_profit:<18}{passed:<6}"
        )

    report = build_validation_report(run)

    _print_header("4. Overall robustness score")
    print(f"Total windows: {report.total_windows}")
    print(f"Completed: {report.completed_windows}")
    print(f"Insufficient data: {report.insufficient_data_windows}")
    print(f"Failed: {report.failed_windows}")
    print(f"Passed: {report.passed_windows}")
    print(f"Robustness score: {report.robustness_score:.2f}%")
    print(f"Overall assessment: {'PASS' if report.overall_passed else 'FAIL'}")
    if report.average_performance_degradation_percent is not None:
        print(f"Average performance degradation: {report.average_performance_degradation_percent:.2f}%")

    _print_header("FULL REPORT (MARKDOWN)")
    print(render_markdown(report))


if __name__ == "__main__":
    main()
