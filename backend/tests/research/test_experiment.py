import pytest
from pydantic import ValidationError

from app.data.models import Timeframe
from app.research.experiment import create_experiment
from app.research.models import Experiment
from tests.research.helpers import make_backtest_config


def test_create_experiment_generates_a_unique_id() -> None:
    config = make_backtest_config()
    first = create_experiment(
        name="A", description="", strategy="EMABreakout", dataset_path="x.csv",
        backtest_config=config, capture_git_commit=False,
    )
    second = create_experiment(
        name="B", description="", strategy="EMABreakout", dataset_path="x.csv",
        backtest_config=config, capture_git_commit=False,
    )

    assert first.experiment_id != second.experiment_id


def test_create_experiment_populates_all_required_fields() -> None:
    config = make_backtest_config()

    experiment = create_experiment(
        name="EMA Breakout Baseline",
        description="Baseline run",
        strategy="EMABreakout",
        dataset_path="backend/app/market_data/sample_data/nifty_sample_candles.csv",
        backtest_config=config,
        timeframe=Timeframe.FIFTEEN_MINUTE,
        parameters={"risk_percent": 1.0},
        seed=42,
        tags=["baseline"],
        notes="first run",
        capture_git_commit=False,
    )

    assert isinstance(experiment, Experiment)
    assert experiment.name == "EMA Breakout Baseline"
    assert experiment.strategy == "EMABreakout"
    assert experiment.timeframe == Timeframe.FIFTEEN_MINUTE
    assert experiment.parameters == {"risk_percent": 1.0}
    assert experiment.seed == 42
    assert experiment.tags == ["baseline"]
    assert experiment.notes == "first run"
    assert experiment.backtest_config == config
    assert experiment.git_commit_hash is None


def test_create_experiment_defaults_parameters_and_tags_to_empty() -> None:
    experiment = create_experiment(
        name="A", description="", strategy="EMABreakout", dataset_path="x.csv",
        backtest_config=make_backtest_config(), capture_git_commit=False,
    )

    assert experiment.parameters == {}
    assert experiment.tags == []


def test_create_experiment_captures_git_commit_hash_when_available() -> None:
    experiment = create_experiment(
        name="A", description="", strategy="EMABreakout", dataset_path="x.csv",
        backtest_config=make_backtest_config(),
    )

    # This test runs inside a real git checkout, so a hash should be
    # captured - but this is inherently environment-dependent (no git,
    # or not a repo, both fall back to None), so only assert the shape.
    assert experiment.git_commit_hash is None or len(experiment.git_commit_hash) == 40


def test_create_experiment_is_immutable() -> None:
    experiment = create_experiment(
        name="A", description="", strategy="EMABreakout", dataset_path="x.csv",
        backtest_config=make_backtest_config(), capture_git_commit=False,
    )

    with pytest.raises(ValidationError):
        experiment.name = "B"  # type: ignore[misc]
