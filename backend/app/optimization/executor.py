"""
Execution orchestration: for every grid combination, build a
`StrategyParameters`/`RiskConfig` pair, create an `Experiment`, run it
through the existing (frozen) `app.research.experiment_runner`, and
collect the result. This module calculates nothing itself - it only
decides what configuration each combination represents and calls into
Phase 14's `create_experiment()`/`run_experiment()`, exactly as those
already call into Phases 9-12 beneath them.

Of the six `DEFAULT_PARAMETER_CATALOG` parameters, three flow straight
into `RiskConfig` (`risk_percent` -> `risk_per_trade_percent`,
`max_trades_per_day` -> `max_trades_per_day`, `reward_risk_ratio` ->
`target_atr_multiplier`, derived below) and two flow into
`StrategyParameters` (`rsi_bullish_threshold`, `rsi_bearish_threshold`).
`ema_period` flows into `BacktestConfig.ema_period` directly. All six
now genuinely change a real backtest outcome - Phase 16 was explicitly
authorized (CTO decision, see docs/OPTIMIZATION_GUIDE.md) to add a
minimal, additive `strategy_parameters`/`ema_period` seam to
`app.trading.backtest.BacktestConfig`/`run_backtest()`, which had none
before this phase (not even `EMABreakoutStrategy`'s own Phase 15
injection point could reach an actual backtest run without it).

`reward_risk_ratio` is applied as
`target_atr_multiplier = reward_risk_ratio * stop_loss_atr_multiplier`,
holding the base configuration's `stop_loss_atr_multiplier` fixed - see
`RiskAssessment.reward_risk_ratio`'s own definition
(`target_distance / stop_loss_distance`, and both distances are
`atr * their own multiplier`, so the multiplier ratio equals the
achieved reward/risk ratio exactly). This is a real, existing risk
relationship, not a new one invented for this package.
"""

import time
import uuid
from datetime import datetime

from app.config.strategy_config import StrategyParameters
from app.optimization.grid_generator import generate_grid
from app.optimization.models import GridValue, OptimizationResult, OptimizationRun
from app.optimization.parameter_space import ParameterSpace
from app.optimization.progress import ProgressTracker
from app.research.experiment import create_experiment
from app.research.experiment_runner import run_experiment
from app.research.models import ExperimentStatus
from app.trading.backtest.models import BacktestConfig


def _apply_combination(
    combination: dict[str, GridValue], *, base_config: BacktestConfig
) -> BacktestConfig:
    base_risk_config = base_config.risk_config

    risk_config = base_risk_config.model_copy(
        update={
            "risk_per_trade_percent": combination.get(
                "risk_percent", base_risk_config.risk_per_trade_percent
            ),
            "max_trades_per_day": int(
                combination.get("max_trades_per_day", base_risk_config.max_trades_per_day)
            ),
            "target_atr_multiplier": (
                combination["reward_risk_ratio"] * base_risk_config.stop_loss_atr_multiplier
                if "reward_risk_ratio" in combination
                else base_risk_config.target_atr_multiplier
            ),
        }
    )

    base_strategy_parameters = base_config.strategy_parameters or StrategyParameters()
    strategy_parameters = base_strategy_parameters.model_copy(
        update={
            key: value
            for key, value in {
                "rsi_bullish_threshold": combination.get("rsi_bullish_threshold"),
                "rsi_bearish_threshold": combination.get("rsi_bearish_threshold"),
            }.items()
            if value is not None
        }
    )

    ema_period = int(combination.get("ema_period", base_config.ema_period))

    return base_config.model_copy(
        update={
            "risk_config": risk_config,
            "strategy_parameters": strategy_parameters,
            "ema_period": ema_period,
        }
    )


def run_grid_search(
    *,
    parameter_space: ParameterSpace,
    dataset_path: str,
    base_backtest_config: BacktestConfig,
    strategy_name: str = "EMABreakout",
    run_id: str | None = None,
) -> OptimizationRun:
    combinations = generate_grid(parameter_space)
    tracker = ProgressTracker(len(combinations))
    start = time.perf_counter()

    results: list[OptimizationResult] = []
    for index, combination in enumerate(combinations):
        combination_id = f"combo-{index:04d}"
        backtest_config = _apply_combination(combination, base_config=base_backtest_config)

        experiment = create_experiment(
            name=combination_id,
            description=", ".join(f"{key}={value}" for key, value in combination.items()),
            strategy=strategy_name,
            dataset_path=dataset_path,
            backtest_config=backtest_config,
            parameters=dict(combination),
            tags=["grid-search"],
        )
        experiment_result = run_experiment(experiment)
        failed = experiment_result.status == ExperimentStatus.FAILED

        results.append(
            OptimizationResult(
                combination_id=combination_id,
                parameter_values=combination,
                experiment_result=experiment_result,
                failed=failed,
                error=experiment_result.error,
            )
        )
        tracker.record(failed=failed)

    duration = time.perf_counter() - start

    return OptimizationRun(
        run_id=run_id if run_id is not None else str(uuid.uuid4()),
        created_date=datetime.now(),
        strategy_name=strategy_name,
        dataset_path=dataset_path,
        parameter_space=parameter_space,
        results=tuple(results),
        total_combinations=len(combinations),
        failed_count=sum(1 for result in results if result.failed),
        duration_seconds=duration,
    )
