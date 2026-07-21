import pytest
from pydantic import ValidationError

from app.config.strategy_config import StrategyParameters


def test_defaults_match_the_values_ema_breakout_previously_hardcoded() -> None:
    params = StrategyParameters()

    assert params.rsi_bullish_threshold == 55.0
    assert params.rsi_bearish_threshold == 45.0
    assert params.vwap_enabled is True
    assert params.supertrend_enabled is True
    assert params.min_agreeing_checks == 4


def test_explicit_values_override_defaults() -> None:
    params = StrategyParameters(rsi_bullish_threshold=60.0, vwap_enabled=False)

    assert params.rsi_bullish_threshold == 60.0
    assert params.vwap_enabled is False


def test_rejects_bearish_threshold_not_below_bullish_threshold() -> None:
    with pytest.raises(ValidationError, match="rsi_bearish_threshold"):
        StrategyParameters(rsi_bullish_threshold=50.0, rsi_bearish_threshold=50.0)


@pytest.mark.parametrize("field", ["rsi_bullish_threshold", "rsi_bearish_threshold"])
def test_rejects_rsi_threshold_out_of_range(field: str) -> None:
    with pytest.raises(ValidationError, match=field):
        StrategyParameters(**{field: 150.0})


def test_rejects_min_agreeing_checks_unreachable_with_both_optional_checks_disabled() -> None:
    with pytest.raises(ValidationError, match="min_agreeing_checks"):
        StrategyParameters(vwap_enabled=False, supertrend_enabled=False, min_agreeing_checks=4)


def test_min_agreeing_checks_of_three_is_valid_with_both_optional_checks_disabled() -> None:
    params = StrategyParameters(vwap_enabled=False, supertrend_enabled=False, min_agreeing_checks=3)

    assert params.min_agreeing_checks == 3


def test_is_immutable() -> None:
    params = StrategyParameters()

    with pytest.raises(ValidationError):
        params.rsi_bullish_threshold = 70.0  # type: ignore[misc]


def test_serializes_to_a_plain_dict_and_round_trips() -> None:
    params = StrategyParameters(rsi_bullish_threshold=58.0)

    dumped = params.model_dump()
    restored = StrategyParameters.model_validate(dumped)

    assert restored == params
