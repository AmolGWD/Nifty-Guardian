"""
Position Variation: randomly resizes each trade's quantity within a
configurable percentage range (e.g. -20% to +20% of its original
size), simulating imperfect position sizing under real execution
(partial fills, rounding to lot sizes, capital availability at the
moment of entry). Only quantity and pnl change - entry/exit price are
untouched. Quantity never drops below 1 - a position of zero isn't a
"smaller trade," it's a trade that didn't happen (see
`missed_trade.py` for that case instead).
"""

import random

from pydantic import BaseModel, ConfigDict, model_validator

from app.config.validation import ParameterValidationError
from app.trading.backtest.models import BacktestTrade
from app.trading.strategy.models import StrategyDirection


class PositionVariationConfig(BaseModel):
    model_config = ConfigDict(frozen=True)

    min_variation_percent: float
    max_variation_percent: float

    @model_validator(mode="after")
    def _validate(self) -> "PositionVariationConfig":
        if self.min_variation_percent >= self.max_variation_percent:
            raise ParameterValidationError(
                "min_variation_percent must be less than max_variation_percent"
            )
        if self.min_variation_percent <= -100:
            raise ParameterValidationError(
                "min_variation_percent must be greater than -100 (cannot shrink a position "
                "by 100% or more)"
            )
        return self


def apply(
    trades: list[BacktestTrade], config: PositionVariationConfig, rng: random.Random
) -> list[BacktestTrade]:
    return [_apply_to_one(trade, config, rng) for trade in trades]


def _apply_to_one(
    trade: BacktestTrade, config: PositionVariationConfig, rng: random.Random
) -> BacktestTrade:
    variation_percent = rng.uniform(config.min_variation_percent, config.max_variation_percent)
    quantity = max(1, round(trade.quantity * (1 + variation_percent / 100)))

    sign = -1 if trade.direction == StrategyDirection.SHORT else 1
    pnl = round((trade.exit_price - trade.entry_price) * quantity * sign, 4)

    return trade.model_copy(update={"quantity": quantity, "pnl": pnl})
