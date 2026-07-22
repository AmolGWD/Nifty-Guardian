"""
Execution Delay: delays both the entry and exit fill of every trade by
N candles, using the original candle series to look up the actual
close price N candles after the fill would have happened - a real
lookup, not an approximation, following the same pattern
`app.trading.analytics.regime_analysis` already established for
needing the original candles as an extra input beyond a
`BacktestResult` (frozen; that precedent, not a new one, motivates
`candles` being a separate argument here rather than something this
package re-derives).

A trade whose delayed fill would fall past the end of the available
candle series keeps its original price for that fill - there is
nothing to look up past the data that exists.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, model_validator

from app.config.validation import ParameterValidationError
from app.market_data.schemas import Candle
from app.trading.backtest.models import BacktestTrade
from app.trading.strategy.models import StrategyDirection

_TimestampIndex = dict[datetime, int]


class ExecutionDelayConfig(BaseModel):
    model_config = ConfigDict(frozen=True)

    delay_candles: int

    @model_validator(mode="after")
    def _validate(self) -> "ExecutionDelayConfig":
        if self.delay_candles <= 0:
            raise ParameterValidationError("delay_candles must be positive")
        return self


def apply(
    trades: list[BacktestTrade], candles: list[Candle], config: ExecutionDelayConfig
) -> list[BacktestTrade]:
    ordered_candles = sorted(candles, key=lambda candle: candle.timestamp)
    index_by_timestamp = {candle.timestamp: index for index, candle in enumerate(ordered_candles)}

    return [_apply_to_one(trade, ordered_candles, index_by_timestamp, config) for trade in trades]


def _apply_to_one(
    trade: BacktestTrade,
    ordered_candles: list[Candle],
    index_by_timestamp: _TimestampIndex,
    config: ExecutionDelayConfig,
) -> BacktestTrade:
    entry_price = _delayed_price(
        ordered_candles, index_by_timestamp, trade.entry_time, config.delay_candles
    )
    exit_price = _delayed_price(
        ordered_candles, index_by_timestamp, trade.exit_time, config.delay_candles
    )
    entry_price = entry_price if entry_price is not None else trade.entry_price
    exit_price = exit_price if exit_price is not None else trade.exit_price

    sign = -1 if trade.direction == StrategyDirection.SHORT else 1
    pnl = round((exit_price - entry_price) * trade.quantity * sign, 4)

    return trade.model_copy(
        update={"entry_price": entry_price, "exit_price": exit_price, "pnl": pnl}
    )


def _delayed_price(
    ordered_candles: list[Candle],
    index_by_timestamp: _TimestampIndex,
    timestamp: datetime,
    delay_candles: int,
) -> float | None:
    index = index_by_timestamp.get(timestamp)
    if index is None:
        return None

    delayed_index = index + delay_candles
    if delayed_index >= len(ordered_candles):
        return None

    return ordered_candles[delayed_index].close
