import pydantic
import pytest

from app.runtime.engine_config import (
    EngineConfig,
    ReplaySpeed,
    TradingSessionMode,
    sleep_seconds_for,
)


def test_defaults() -> None:
    config = EngineConfig()
    assert config.replay_speed == ReplaySpeed.UNLIMITED
    assert config.maximum_candles is None
    assert config.auto_stop_on_completion is True
    assert config.trading_session_mode == TradingSessionMode.REPLAY
    assert config.logging_level == "INFO"
    assert config.random_seed == 0


def test_frozen() -> None:
    config = EngineConfig()
    with pytest.raises(pydantic.ValidationError):
        config.random_seed = 5  # type: ignore[misc]


@pytest.mark.parametrize("maximum_candles", [0, -1, -100])
def test_rejects_non_positive_maximum_candles(maximum_candles: int) -> None:
    with pytest.raises(pydantic.ValidationError, match="maximum_candles must be positive"):
        EngineConfig(maximum_candles=maximum_candles)


def test_accepts_positive_maximum_candles() -> None:
    assert EngineConfig(maximum_candles=10).maximum_candles == 10


def test_rejects_invalid_logging_level() -> None:
    with pytest.raises(pydantic.ValidationError, match="logging_level"):
        EngineConfig(logging_level="VERBOSE")


@pytest.mark.parametrize("level", ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
def test_accepts_valid_logging_levels(level: str) -> None:
    assert EngineConfig(logging_level=level).logging_level == level


@pytest.mark.parametrize(
    ("speed", "expected_multiplier"),
    [
        (ReplaySpeed.X1, 1.0),
        (ReplaySpeed.X2, 2.0),
        (ReplaySpeed.X5, 5.0),
        (ReplaySpeed.X10, 10.0),
    ],
)
def test_sleep_seconds_for_scales_by_multiplier(
    speed: ReplaySpeed, expected_multiplier: float
) -> None:
    interval = 900.0  # 15 minutes
    assert sleep_seconds_for(interval, speed) == interval / expected_multiplier


def test_sleep_seconds_for_unlimited_is_always_zero() -> None:
    assert sleep_seconds_for(900.0, ReplaySpeed.UNLIMITED) == 0.0
    assert sleep_seconds_for(0.0, ReplaySpeed.UNLIMITED) == 0.0
