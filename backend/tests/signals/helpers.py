from datetime import datetime

from app.market_data.schemas import Candle
from app.paper_trading.models import Order, OrderStatus, Position, PositionStatus
from app.trading.strategy.models import StrategyDirection, StrategyEvaluation, StrategyStrength


def make_evaluation(**overrides: object) -> StrategyEvaluation:
    base: dict[str, object] = dict(
        strategy_name="EMABreakout",
        valid=True,
        direction=StrategyDirection.LONG,
        strength=StrategyStrength.STRONG,
        reasons=[
            "EMA alignment: price above EMA",
            "RSI confirmation: RSI 62.00 above 55",
            "VWAP confirmation: price above VWAP",
            "SuperTrend confirmation: bullish",
            "Trend agreement: Market Context trend is bullish",
        ],
        warnings=[],
    )
    base.update(overrides)
    return StrategyEvaluation(**base)


def make_order(**overrides: object) -> Order:
    base: dict[str, object] = dict(
        order_id="order-1",
        strategy_name="EMABreakout",
        direction=StrategyDirection.LONG,
        requested_price=100.0,
        requested_quantity=50,
        filled_quantity=50,
        average_fill_price=100.0,
        stop_loss=95.0,
        target=115.0,
        status=OrderStatus.FILLED,
        created_at=datetime(2026, 1, 5, 9, 30),
        updated_at=datetime(2026, 1, 5, 9, 30),
    )
    base.update(overrides)
    return Order(**base)


def make_position(**overrides: object) -> Position:
    base: dict[str, object] = dict(
        position_id="pos-1",
        strategy_name="EMABreakout",
        direction=StrategyDirection.LONG,
        average_entry_price=100.0,
        quantity=50,
        initial_quantity=50,
        realized_pnl=0.0,
        unrealized_pnl=0.0,
        status=PositionStatus.OPEN,
        opened_at=datetime(2026, 1, 5, 9, 30),
    )
    base.update(overrides)
    return Position(**base)


def make_candle(**overrides: object) -> Candle:
    base: dict[str, object] = dict(
        timestamp=datetime(2026, 1, 5, 10, 0),
        open=100.0,
        high=101.0,
        low=99.0,
        close=100.0,
        volume=1000,
    )
    base.update(overrides)
    return Candle(**base)
