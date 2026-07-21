import pytest
from pydantic import ValidationError

from app.optimization.parameter_space import (
    DEFAULT_PARAMETER_CATALOG,
    EMA_PERIOD,
    MAX_TRADES_PER_DAY,
    REWARD_RISK_RATIO,
    RISK_PERCENT,
    RSI_BEARISH_THRESHOLD,
    RSI_BULLISH_THRESHOLD,
    OptimizableParameter,
    ParameterSpace,
    ParameterType,
)


def test_ema_period_values_match_the_ctos_example() -> None:
    assert EMA_PERIOD.values() == (10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30)


def test_rsi_bullish_threshold_values_match_the_ctos_example() -> None:
    assert RSI_BULLISH_THRESHOLD.values() == (50.0, 55.0, 60.0)


def test_reward_risk_ratio_values_match_the_ctos_example() -> None:
    assert REWARD_RISK_RATIO.values() == (1.5, 2.0, 2.5)


def test_default_catalog_has_exactly_the_six_named_parameters() -> None:
    names = {parameter.name for parameter in DEFAULT_PARAMETER_CATALOG}
    assert names == {
        "ema_period",
        "rsi_bullish_threshold",
        "rsi_bearish_threshold",
        "reward_risk_ratio",
        "risk_percent",
        "max_trades_per_day",
    }


def test_every_default_catalog_entry_is_safe_to_optimize() -> None:
    assert all(parameter.safe_to_optimize for parameter in DEFAULT_PARAMETER_CATALOG)


@pytest.mark.parametrize(
    "name",
    [
        "vwap_enabled",
        "supertrend_enabled",
        "opening_range_minutes",
        "no_trade_zone_minutes",
        "trading_start_time",
        "trading_end_time",
        "lunch_filter_enabled",
        "allow_expiry_day_trading",
    ],
)
def test_excluded_parameters_cannot_be_constructed(name: str) -> None:
    with pytest.raises(ValidationError, match="Do NOT optimize"):
        OptimizableParameter(
            name=name,
            description="excluded",
            parameter_type=ParameterType.FLOAT,
            minimum=0,
            maximum=1,
            step=1,
            default=0,
            safe_to_optimize=True,
        )


def test_rejects_non_positive_step() -> None:
    with pytest.raises(ValidationError, match="step"):
        OptimizableParameter(
            name="x", description="d", parameter_type=ParameterType.FLOAT,
            minimum=0, maximum=10, step=0, default=5, safe_to_optimize=True,
        )


def test_rejects_minimum_not_less_than_maximum() -> None:
    with pytest.raises(ValidationError, match="minimum"):
        OptimizableParameter(
            name="x", description="d", parameter_type=ParameterType.FLOAT,
            minimum=10, maximum=10, step=1, default=10, safe_to_optimize=True,
        )


def test_rejects_default_outside_range() -> None:
    with pytest.raises(ValidationError, match="default"):
        OptimizableParameter(
            name="x", description="d", parameter_type=ParameterType.FLOAT,
            minimum=0, maximum=10, step=1, default=20, safe_to_optimize=True,
        )


def test_parameter_space_rejects_empty() -> None:
    with pytest.raises(ValidationError, match="at least one"):
        ParameterSpace(parameters=())


def test_parameter_space_rejects_duplicate_names() -> None:
    with pytest.raises(ValidationError, match="duplicate"):
        ParameterSpace(parameters=(EMA_PERIOD, EMA_PERIOD))


def test_parameter_space_total_combinations() -> None:
    space = ParameterSpace(parameters=(RSI_BULLISH_THRESHOLD, REWARD_RISK_RATIO))
    assert space.total_combinations() == 3 * 3


def test_parameter_space_dimension_names() -> None:
    space = ParameterSpace(parameters=(RISK_PERCENT, MAX_TRADES_PER_DAY))
    assert space.dimension_names() == ("risk_percent", "max_trades_per_day")


def test_rsi_bearish_threshold_default_matches_strategy_default() -> None:
    assert RSI_BEARISH_THRESHOLD.default == 45.0


def test_is_immutable() -> None:
    with pytest.raises(ValidationError):
        EMA_PERIOD.default = 25  # type: ignore[misc]
