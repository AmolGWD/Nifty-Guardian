"""
Runtime Engine configuration - replay speed, candle limits, auto-stop,
trading session mode, logging level, and a random seed. This module
computes nothing about strategies/risk/indicators - it only shapes how
the engine drives itself.
"""

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, model_validator

from app.config.validation import ParameterValidationError


class ReplaySpeed(StrEnum):
    X1 = "1x"
    X2 = "2x"
    X5 = "5x"
    X10 = "10x"
    UNLIMITED = "Unlimited"


_SPEED_MULTIPLIERS: dict[ReplaySpeed, float | None] = {
    ReplaySpeed.X1: 1.0,
    ReplaySpeed.X2: 2.0,
    ReplaySpeed.X5: 5.0,
    ReplaySpeed.X10: 10.0,
    ReplaySpeed.UNLIMITED: None,
}


def sleep_seconds_for(candle_interval_seconds: float, speed: ReplaySpeed) -> float:
    """
    Wall-clock delay between processed candles for a given replay
    speed - `UNLIMITED` always means zero delay (process as fast as
    possible), regardless of candle interval.
    """
    multiplier = _SPEED_MULTIPLIERS[speed]
    if multiplier is None:
        return 0.0
    return candle_interval_seconds / multiplier


class TradingSessionMode(StrEnum):
    """
    Whether the engine treats every candle as tradeable (REPLAY - the
    only mode this phase actually exercises, since there is no live
    feed) or gates entries on a real session clock (LIVE_HOURS -
    reserved for the eventual live deployment `docs/ENGINE_RUNTIME.md`
    describes; nothing in this phase implements it beyond the name,
    since there is no live feed to gate yet).
    """

    REPLAY = "Replay"
    LIVE_HOURS = "LiveHours"


class EngineConfig(BaseModel):
    model_config = ConfigDict(frozen=True)

    replay_speed: ReplaySpeed = ReplaySpeed.UNLIMITED
    maximum_candles: int | None = None
    auto_stop_on_completion: bool = True
    trading_session_mode: TradingSessionMode = TradingSessionMode.REPLAY
    logging_level: str = "INFO"
    random_seed: int = 0

    @model_validator(mode="after")
    def _validate(self) -> "EngineConfig":
        if self.maximum_candles is not None and self.maximum_candles <= 0:
            raise ParameterValidationError("maximum_candles must be positive when set")
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if self.logging_level not in valid_levels:
            raise ParameterValidationError(
                f"logging_level={self.logging_level!r} must be one of {sorted(valid_levels)}"
            )
        return self
