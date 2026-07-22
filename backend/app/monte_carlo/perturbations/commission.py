"""
Commission: subtracts a configurable brokerage cost from every trade's
pnl - a percentage of the round-trip notional (entry value + exit
value), a flat currency amount per trade, or both together. Neither
price nor quantity is touched; only pnl changes.
"""

from pydantic import BaseModel, ConfigDict, model_validator

from app.config.validation import ParameterValidationError
from app.trading.backtest.models import BacktestTrade


class CommissionConfig(BaseModel):
    model_config = ConfigDict(frozen=True)

    commission_percent: float = 0.0
    flat_commission_per_trade: float = 0.0

    @model_validator(mode="after")
    def _validate(self) -> "CommissionConfig":
        if self.commission_percent < 0:
            raise ParameterValidationError("commission_percent cannot be negative")
        if self.flat_commission_per_trade < 0:
            raise ParameterValidationError("flat_commission_per_trade cannot be negative")
        return self


def apply(trades: list[BacktestTrade], config: CommissionConfig) -> list[BacktestTrade]:
    return [_apply_to_one(trade, config) for trade in trades]


def _apply_to_one(trade: BacktestTrade, config: CommissionConfig) -> BacktestTrade:
    round_trip_notional = (trade.entry_price + trade.exit_price) * trade.quantity
    cost = round_trip_notional * config.commission_percent / 100 + config.flat_commission_per_trade
    pnl = round(trade.pnl - cost, 4)
    return trade.model_copy(update={"pnl": pnl})
