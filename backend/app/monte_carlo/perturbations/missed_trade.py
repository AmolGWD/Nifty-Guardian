"""
Missed Trades: randomly drops each trade independently with a
configurable probability, simulating fills that never happened
(a rejected order, a connectivity gap, a signal that arrived too late
to act on). The remaining trades are otherwise untouched.
"""

import random

from pydantic import BaseModel, ConfigDict, model_validator

from app.config.validation import ParameterValidationError
from app.trading.backtest.models import BacktestTrade


class MissedTradeConfig(BaseModel):
    model_config = ConfigDict(frozen=True)

    miss_probability_percent: float

    @model_validator(mode="after")
    def _validate(self) -> "MissedTradeConfig":
        if not (0 <= self.miss_probability_percent <= 100):
            raise ParameterValidationError("miss_probability_percent must be within [0, 100]")
        return self


def apply(
    trades: list[BacktestTrade], config: MissedTradeConfig, rng: random.Random
) -> list[BacktestTrade]:
    return [trade for trade in trades if rng.uniform(0, 100) >= config.miss_probability_percent]
