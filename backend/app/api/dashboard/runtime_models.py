"""Request models for POST /api/runtime/*."""

from pydantic import BaseModel, ConfigDict

from app.runtime.engine_config import ReplaySpeed


class ReplayRequest(BaseModel):
    model_config = ConfigDict(frozen=True)

    replay_speed: ReplaySpeed = ReplaySpeed.X1
    maximum_candles: int | None = None


class RuntimeStateResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    state: str
