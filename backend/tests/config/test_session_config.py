import pytest
from pydantic import ValidationError

from app.config.session_config import SessionParameters


def test_defaults_mirror_build_trading_conditions_own_existing_defaults() -> None:
    params = SessionParameters()

    assert params.opening_range_minutes == 15
    assert params.no_trade_zone_minutes == 15
    assert params.trading_start_time == "09:15"
    assert params.trading_end_time == "15:30"
    assert params.allow_expiry_day_trading is True
    assert params.lunch_filter_enabled is False


def test_rejects_invalid_time_format() -> None:
    with pytest.raises(ValidationError, match="trading_start_time"):
        SessionParameters(trading_start_time="9:15am")


def test_rejects_start_time_not_before_end_time() -> None:
    with pytest.raises(ValidationError, match="trading_start_time"):
        SessionParameters(trading_start_time="15:30", trading_end_time="09:15")


def test_is_immutable() -> None:
    params = SessionParameters()

    with pytest.raises(ValidationError):
        params.opening_range_minutes = 30  # type: ignore[misc]


def test_serializes_to_a_plain_dict_and_round_trips() -> None:
    params = SessionParameters(opening_range_minutes=30)

    dumped = params.model_dump()
    restored = SessionParameters.model_validate(dumped)

    assert restored == params
