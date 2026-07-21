"""
Simulates the lifecycle of one open position against subsequent
candles: entry (from a `TradeRecommendation`), then stop-loss, target,
or end-of-day exit. Long-only for this phase, per the CTO brief -
`build_open_position` is only ever called by `backtest_engine.py` when
`TradeRecommendation.direction` is `Long`.

Performs no indicator, strategy, or risk calculation of its own - it
only reads the entry price/stop-loss/target/quantity that the existing
pipeline (Risk Engine, via `RiskAssessment`) already computed, and
mechanically decides when that position closes.

Stop-loss is checked before target when a single candle's range could
plausibly satisfy both (a conservative assumption about the worst
intrabar path, common practice in backtesting since OHLC candles alone
don't reveal which level was actually touched first).
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.market_data.schemas import Candle
from app.trading.backtest.models import BacktestTrade, ExitReason
from app.trading.decision.models import TradeRecommendation
from app.trading.strategy.models import StrategyDirection


class OpenPosition(BaseModel):
    model_config = ConfigDict(frozen=True)

    strategy_name: str
    direction: StrategyDirection

    entry_time: datetime
    entry_price: float

    stop_loss: float
    target: float
    quantity: int
    planned_reward_risk_ratio: float


def build_open_position(
    recommendation: TradeRecommendation, entry_time: datetime, entry_price: float
) -> OpenPosition:
    assert recommendation.recommended
    assert recommendation.direction == StrategyDirection.LONG
    assert recommendation.selected_strategy is not None
    assert recommendation.risk_summary is not None

    return OpenPosition(
        strategy_name=recommendation.selected_strategy,
        direction=recommendation.direction,
        entry_time=entry_time,
        entry_price=entry_price,
        stop_loss=recommendation.risk_summary.stop_loss,
        target=recommendation.risk_summary.target,
        quantity=recommendation.risk_summary.position_size,
        planned_reward_risk_ratio=recommendation.risk_summary.reward_risk_ratio,
    )


def check_exit(position: OpenPosition, candle: Candle, market_close: str) -> BacktestTrade | None:
    if candle.low <= position.stop_loss:
        return _close(position, candle.timestamp, position.stop_loss, ExitReason.STOP_LOSS)

    if candle.high >= position.target:
        return _close(position, candle.timestamp, position.target, ExitReason.TARGET)

    if candle.timestamp.strftime("%H:%M") >= market_close:
        return _close(position, candle.timestamp, candle.close, ExitReason.END_OF_DAY)

    return None


def force_close(position: OpenPosition, candle: Candle) -> BacktestTrade:
    return _close(position, candle.timestamp, candle.close, ExitReason.END_OF_DATA)


def _close(
    position: OpenPosition, exit_time: datetime, exit_price: float, reason: ExitReason
) -> BacktestTrade:
    pnl = (exit_price - position.entry_price) * position.quantity

    return BacktestTrade(
        strategy_name=position.strategy_name,
        direction=position.direction,
        entry_time=position.entry_time,
        entry_price=position.entry_price,
        exit_time=exit_time,
        exit_price=exit_price,
        exit_reason=reason,
        quantity=position.quantity,
        stop_loss=position.stop_loss,
        target=position.target,
        planned_reward_risk_ratio=position.planned_reward_risk_ratio,
        pnl=round(pnl, 4),
    )
