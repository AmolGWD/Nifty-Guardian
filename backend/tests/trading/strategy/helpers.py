from datetime import datetime

from app.trading.conditions.models import NoTradeReason, TradingConditions


def make_trading_conditions(
    *,
    can_trade: bool = True,
    no_trade_reason: NoTradeReason | None = None,
) -> TradingConditions:
    return TradingConditions(
        as_of=datetime(2026, 7, 21, 11, 0),
        can_trade=can_trade,
        no_trade_reason=no_trade_reason,
        session_valid=True,
        opening_range_complete=True,
        within_trading_window=True,
        expiry_allowed=True,
        liquidity_ok=True,
        cooldown_complete=True,
        gap_filter_ok=True,
        position_guard_ok=True,
    )
