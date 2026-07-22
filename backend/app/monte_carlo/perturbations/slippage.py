"""
Slippage: worsens every trade's entry and exit fill price by a
configurable percentage, then recomputes that trade's pnl from the
adjusted prices - the same `(exit - entry) * quantity` (sign-adjusted
for direction) formula `app.trading.backtest.trade_executor._close()`
already uses, not a new one.

"Worse" means the direction that actually costs money: a Long entry
fills higher than quoted, a Long exit fills lower; a Short entry fills
lower, a Short exit fills higher. Slippage never helps a fill in this
model - real slippage is adverse by definition.
"""

from pydantic import BaseModel, ConfigDict, model_validator

from app.config.validation import ParameterValidationError
from app.trading.backtest.models import BacktestTrade
from app.trading.strategy.models import StrategyDirection


class SlippageConfig(BaseModel):
    model_config = ConfigDict(frozen=True)

    entry_slippage_percent: float
    exit_slippage_percent: float

    @model_validator(mode="after")
    def _validate(self) -> "SlippageConfig":
        if self.entry_slippage_percent < 0:
            raise ParameterValidationError("entry_slippage_percent cannot be negative")
        if self.exit_slippage_percent < 0:
            raise ParameterValidationError("exit_slippage_percent cannot be negative")
        return self


def apply(trades: list[BacktestTrade], config: SlippageConfig) -> list[BacktestTrade]:
    return [_apply_to_one(trade, config) for trade in trades]


def _apply_to_one(trade: BacktestTrade, config: SlippageConfig) -> BacktestTrade:
    if trade.direction == StrategyDirection.SHORT:
        entry_price = trade.entry_price * (1 - config.entry_slippage_percent / 100)
        exit_price = trade.exit_price * (1 + config.exit_slippage_percent / 100)
        sign = -1
    else:
        entry_price = trade.entry_price * (1 + config.entry_slippage_percent / 100)
        exit_price = trade.exit_price * (1 - config.exit_slippage_percent / 100)
        sign = 1

    pnl = round((exit_price - entry_price) * trade.quantity * sign, 4)
    return trade.model_copy(
        update={"entry_price": entry_price, "exit_price": exit_price, "pnl": pnl}
    )
