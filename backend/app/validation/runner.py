"""
Walk-Forward Validation orchestration: for every generated window,
slice the dataset into train/test candle subsets, run the existing
(frozen) Grid Search Optimization Engine on the training subset only,
take its best configuration, then run the existing (frozen) Experiment
Framework (Backtest Engine + Analytics Engine) with that exact
configuration against the testing subset only, and compare.

This module calculates no indicator, strategy, risk, backtest, or
analytics value itself - every one of those is a call into the
package that already owns it (Phases 5-16). It only decides *what data
each phase sees* (train vs. test) and orchestrates the sequence.

Train/test subsets are written to temporary CSV files (cleaned up when
the run finishes) because `app.optimization`/`app.research`'s existing,
frozen APIs are file-path-based
(`app.trading.backtest.loader.load_candles_from_csv`) - this is I/O
plumbing to interface with that existing contract, not a reimplementation
of anything those packages already do.
"""

import csv
import tempfile
import time
import uuid
from datetime import datetime
from pathlib import Path

from app.market_data.schemas import Candle
from app.optimization.optimizer import optimize
from app.optimization.parameter_space import ParameterSpace
from app.optimization.ranking import RankBy
from app.research.experiment import create_experiment
from app.research.experiment_runner import run_experiment
from app.research.models import ExperimentStatus, ParameterValue
from app.research.scoring import ScoringWeights
from app.trading.backtest.loader import load_candles_from_csv
from app.trading.backtest.models import BacktestConfig
from app.validation.models import (
    ValidationResult,
    ValidationRules,
    ValidationRun,
    Window,
    WindowConfig,
    WindowStatus,
)
from app.validation.validator import evaluate_pass_fail
from app.validation.window_generator import generate_windows


def run_walk_forward_validation(
    *,
    window_config: WindowConfig,
    parameter_space: ParameterSpace,
    validation_rules: ValidationRules,
    dataset_path: str,
    base_backtest_config: BacktestConfig,
    strategy_name: str = "EMABreakout",
    rank_by: RankBy = RankBy.WEIGHTED_SCORE,
    weights: ScoringWeights | None = None,
) -> ValidationRun:
    start = time.perf_counter()
    all_candles = load_candles_from_csv(dataset_path)
    if not all_candles:
        raise ValueError(f"Dataset {dataset_path!r} contains no candles")

    data_start = min(candle.timestamp for candle in all_candles)
    data_end = max(candle.timestamp for candle in all_candles)
    windows = generate_windows(window_config, data_start=data_start, data_end=data_end)

    results: list[ValidationResult] = []
    with tempfile.TemporaryDirectory(prefix="walk-forward-") as temp_dir:
        for window in windows:
            results.append(
                _validate_one_window(
                    window,
                    window_config=window_config,
                    parameter_space=parameter_space,
                    validation_rules=validation_rules,
                    all_candles=all_candles,
                    base_backtest_config=base_backtest_config,
                    strategy_name=strategy_name,
                    rank_by=rank_by,
                    weights=weights,
                    temp_dir=Path(temp_dir),
                )
            )

    return ValidationRun(
        run_id=str(uuid.uuid4()),
        created_date=datetime.now(),
        strategy_name=strategy_name,
        dataset_path=dataset_path,
        window_config=window_config,
        validation_rules=validation_rules,
        results=tuple(results),
        duration_seconds=time.perf_counter() - start,
    )


def _validate_one_window(
    window: Window,
    *,
    window_config: WindowConfig,
    parameter_space: ParameterSpace,
    validation_rules: ValidationRules,
    all_candles: list[Candle],
    base_backtest_config: BacktestConfig,
    strategy_name: str,
    rank_by: RankBy,
    weights: ScoringWeights | None,
    temp_dir: Path,
) -> ValidationResult:
    train_candles = _candles_in_range(all_candles, window.train_start, window.train_end)
    test_candles = _candles_in_range(all_candles, window.test_start, window.test_end)

    if (
        len(train_candles) < window_config.minimum_candles
        or len(test_candles) < window_config.minimum_candles
    ):
        return ValidationResult(
            window=window,
            status=WindowStatus.INSUFFICIENT_DATA,
            best_parameter_values=None,
            train_result=None,
            test_result=None,
            pass_fail=None,
            error=(
                f"train has {len(train_candles)} candles, test has {len(test_candles)} "
                f"candles - minimum required is {window_config.minimum_candles}"
            ),
        )

    train_csv = temp_dir / f"window-{window.window_index:04d}-train.csv"
    test_csv = temp_dir / f"window-{window.window_index:04d}-test.csv"
    _write_candles_csv(train_candles, train_csv)
    _write_candles_csv(test_candles, test_csv)

    try:
        _, ranked, _ = optimize(
            parameter_space=parameter_space,
            dataset_path=str(train_csv),
            base_backtest_config=base_backtest_config,
            strategy_name=strategy_name,
            rank_by=rank_by,
            weights=weights,
        )
    except Exception as error:  # noqa: BLE001 - a bad window is a real, expected outcome
        return ValidationResult(
            window=window,
            status=WindowStatus.FAILED,
            best_parameter_values=None,
            train_result=None,
            test_result=None,
            pass_fail=None,
            error=str(error),
        )

    completed_ranked = [
        ranked_result
        for ranked_result in ranked
        if ranked_result.result.experiment_result.status == ExperimentStatus.COMPLETED
    ]
    if not completed_ranked:
        return ValidationResult(
            window=window,
            status=WindowStatus.INSUFFICIENT_DATA,
            best_parameter_values=None,
            train_result=None,
            test_result=None,
            pass_fail=None,
            error="every training combination failed - no best configuration to test",
        )

    best = completed_ranked[0]
    best_train_result = best.result.experiment_result
    train_backtest_result = best_train_result.backtest_result
    assert train_backtest_result is not None  # COMPLETED always has one

    if train_backtest_result.report.total_trades < window_config.minimum_trades:
        return ValidationResult(
            window=window,
            status=WindowStatus.INSUFFICIENT_DATA,
            best_parameter_values=best.result.parameter_values,
            train_result=best_train_result,
            test_result=None,
            pass_fail=None,
            error=(
                f"best training configuration made only "
                f"{train_backtest_result.report.total_trades} trades - minimum required is "
                f"{window_config.minimum_trades}"
            ),
        )

    best_backtest_config = best_train_result.experiment.backtest_config
    test_parameters: dict[str, ParameterValue] = dict(best.result.parameter_values)
    test_experiment = create_experiment(
        name=f"window-{window.window_index:04d}-test",
        description=f"Walk-forward test for {best.result.combination_id}",
        strategy=strategy_name,
        dataset_path=str(test_csv),
        backtest_config=best_backtest_config,
        parameters=test_parameters,
        tags=["walk-forward", "test"],
    )
    test_result = run_experiment(test_experiment)

    if test_result.status == ExperimentStatus.FAILED:
        return ValidationResult(
            window=window,
            status=WindowStatus.FAILED,
            best_parameter_values=best.result.parameter_values,
            train_result=best_train_result,
            test_result=test_result,
            pass_fail=None,
            error=test_result.error,
        )

    assert best_train_result.analytics_report is not None
    assert test_result.analytics_report is not None
    pass_fail = evaluate_pass_fail(
        best_train_result.analytics_report.overall,
        test_result.analytics_report.overall,
        validation_rules,
    )

    return ValidationResult(
        window=window,
        status=WindowStatus.COMPLETED,
        best_parameter_values=best.result.parameter_values,
        train_result=best_train_result,
        test_result=test_result,
        pass_fail=pass_fail,
        error=None,
    )


def _candles_in_range(
    candles: list[Candle], start: datetime, end: datetime
) -> list[Candle]:
    return [candle for candle in candles if start <= candle.timestamp < end]


def _write_candles_csv(candles: list[Candle], path: Path) -> None:
    with open(path, "w", newline="", encoding="utf-8") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(["Timestamp", "Open", "High", "Low", "Close", "Volume"])
        for candle in candles:
            writer.writerow(
                [
                    candle.timestamp.isoformat(),
                    candle.open,
                    candle.high,
                    candle.low,
                    candle.close,
                    candle.volume,
                ]
            )
