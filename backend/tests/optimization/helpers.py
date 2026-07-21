from app.optimization.models import GridValue, OptimizationResult
from app.research.models import ExperimentStatus
from tests.research.helpers import make_synthetic_result


def make_optimization_result(
    *,
    combination_id: str = "combo-0000",
    parameter_values: dict[str, GridValue] | None = None,
    net_profit: float = 1_000.0,
    profit_factor: float | None = 2.0,
    max_drawdown: float = 500.0,
    recovery_factor: float | None = 2.0,
    sharpe_ratio: float | None = 1.5,
    win_rate: float = 55.0,
    failed: bool = False,
) -> OptimizationResult:
    values = parameter_values if parameter_values is not None else {"ema_period": 20}

    experiment_result = make_synthetic_result(
        name=combination_id,
        net_profit=net_profit,
        profit_factor=profit_factor,
        max_drawdown=max_drawdown,
        recovery_factor=recovery_factor,
        sharpe_ratio=sharpe_ratio,
        win_rate=win_rate,
        status=ExperimentStatus.FAILED if failed else ExperimentStatus.COMPLETED,
    )
    # make_synthetic_result() doesn't accept `parameters` - mirror what
    # executor.py actually does (create_experiment(parameters=combination))
    # by attaching the grid values onto the already-built Experiment.
    updated_experiment = experiment_result.experiment.model_copy(
        update={"parameters": values}
    )
    experiment_result = experiment_result.model_copy(update={"experiment": updated_experiment})

    return OptimizationResult(
        combination_id=combination_id,
        parameter_values=values,
        experiment_result=experiment_result,
        failed=failed,
        error=experiment_result.error,
    )
