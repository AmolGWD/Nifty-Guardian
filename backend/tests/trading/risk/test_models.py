import pytest
from pydantic import ValidationError

from app.config.validation import ParameterValidationError
from app.trading.risk.models import RiskConfig


def test_default_construction_matches_every_existing_test_helper_default() -> None:
    config = RiskConfig()

    assert config.risk_per_trade_percent == 1.0
    assert config.stop_loss_atr_multiplier == 1.5
    assert config.target_atr_multiplier == 3.0
    assert config.max_daily_loss == 5_000.0
    assert config.max_trades_per_day == 5
    assert config.max_concurrent_positions == 1
    assert config.max_capital_exposure_percent == 50.0


def test_explicit_values_still_override_defaults() -> None:
    config = RiskConfig(risk_per_trade_percent=2.0, max_trades_per_day=10)

    assert config.risk_per_trade_percent == 2.0
    assert config.max_trades_per_day == 10


@pytest.mark.parametrize(
    "field,invalid_value",
    [
        ("risk_per_trade_percent", 0.0),
        ("risk_per_trade_percent", 10.0),
        ("stop_loss_atr_multiplier", 0.1),
        ("target_atr_multiplier", 20.0),
        ("max_daily_loss", -1.0),
        ("max_trades_per_day", 0),
        ("max_concurrent_positions", 0),
        ("max_capital_exposure_percent", 0.5),
        ("max_capital_exposure_percent", 200.0),
    ],
)
def test_out_of_range_values_are_rejected_with_a_meaningful_message(
    field: str, invalid_value: float
) -> None:
    with pytest.raises(ValidationError) as excinfo:
        RiskConfig(**{field: invalid_value})

    assert isinstance(excinfo.value.errors()[0]["ctx"]["error"], ParameterValidationError)
    assert field in str(excinfo.value)


def test_risk_config_is_immutable() -> None:
    config = RiskConfig()

    with pytest.raises(ValidationError):
        config.max_trades_per_day = 99  # type: ignore[misc]
