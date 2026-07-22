import pytest
from pydantic import ValidationError

from app.validation.models import ValidationRules, WindowConfig, WindowType


def _valid_window_config(**overrides: object) -> dict[str, object]:
    base = dict(
        window_type=WindowType.ROLLING,
        training_duration_days=2,
        testing_duration_days=1,
        step_size_days=1,
        minimum_candles=10,
        minimum_trades=1,
    )
    base.update(overrides)
    return base


def test_window_config_accepts_valid_values() -> None:
    config = WindowConfig(**_valid_window_config())
    assert config.window_type == WindowType.ROLLING


@pytest.mark.parametrize(
    "field", ["training_duration_days", "testing_duration_days", "step_size_days"]
)
def test_window_config_rejects_non_positive_durations(field: str) -> None:
    with pytest.raises(ValidationError, match=field):
        WindowConfig(**_valid_window_config(**{field: 0}))


@pytest.mark.parametrize("field", ["minimum_candles", "minimum_trades"])
def test_window_config_rejects_negative_minimums(field: str) -> None:
    with pytest.raises(ValidationError, match=field):
        WindowConfig(**_valid_window_config(**{field: -1}))


def test_window_config_is_immutable() -> None:
    config = WindowConfig(**_valid_window_config())
    with pytest.raises(ValidationError):
        config.training_duration_days = 99  # type: ignore[misc]


def _valid_rules(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = dict(
        max_drawdown_increase_percent=50.0,
        min_profit_factor=1.2,
        max_performance_degradation_percent=30.0,
        min_trade_count=20,
        min_robustness_score_percent=60.0,
    )
    base.update(overrides)
    return base


def test_validation_rules_accepts_valid_values() -> None:
    rules = ValidationRules(**_valid_rules())
    assert rules.min_profit_factor == 1.2


@pytest.mark.parametrize(
    "field",
    [
        "max_drawdown_increase_percent",
        "min_profit_factor",
        "max_performance_degradation_percent",
        "min_trade_count",
    ],
)
def test_validation_rules_rejects_negative_values(field: str) -> None:
    with pytest.raises(ValidationError, match=field):
        ValidationRules(**_valid_rules(**{field: -1}))


@pytest.mark.parametrize("value", [-1.0, 101.0])
def test_validation_rules_rejects_robustness_percent_out_of_range(value: float) -> None:
    with pytest.raises(ValidationError, match="min_robustness_score_percent"):
        ValidationRules(**_valid_rules(min_robustness_score_percent=value))


def test_validation_rules_is_immutable() -> None:
    rules = ValidationRules(**_valid_rules())
    with pytest.raises(ValidationError):
        rules.min_profit_factor = 5.0  # type: ignore[misc]


def test_validation_rules_has_no_defaults() -> None:
    """'Do NOT hardcode thresholds' (CTO brief) - every rule must be supplied explicitly."""
    with pytest.raises(ValidationError):
        ValidationRules()  # type: ignore[call-arg]
