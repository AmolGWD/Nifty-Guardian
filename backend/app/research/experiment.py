"""
Creates `Experiment` definitions - the one place `experiment_id`
generation, `created_date` capture, and best-effort git commit hash
capture happen, so every other module just consumes an already-built
`Experiment`.
"""

import subprocess
import uuid
from datetime import datetime

from app.data.models import Timeframe
from app.research.models import Experiment, ParameterValue
from app.trading.backtest.models import BacktestConfig


def create_experiment(
    *,
    name: str,
    description: str,
    strategy: str,
    dataset_path: str,
    backtest_config: BacktestConfig,
    timeframe: Timeframe = Timeframe.FIFTEEN_MINUTE,
    parameters: dict[str, ParameterValue] | None = None,
    seed: int | None = None,
    tags: list[str] | None = None,
    notes: str = "",
    capture_git_commit: bool = True,
) -> Experiment:
    return Experiment(
        experiment_id=str(uuid.uuid4()),
        name=name,
        description=description,
        created_date=datetime.now(),
        strategy=strategy,
        dataset_path=dataset_path,
        timeframe=timeframe,
        parameters=parameters if parameters is not None else {},
        seed=seed,
        backtest_config=backtest_config,
        tags=tags if tags is not None else [],
        notes=notes,
        git_commit_hash=_current_git_commit_hash() if capture_git_commit else None,
    )


def _current_git_commit_hash() -> str | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None

    if result.returncode != 0:
        return None

    return result.stdout.strip() or None
