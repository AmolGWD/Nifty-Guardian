"""
Composes the independent condition evaluators into one TradingConditions.

no_trade_reason reports the first failing condition in a fixed
priority order (session/timing gates first, then position/cooldown,
then gap/liquidity) - not every failing condition at once, since the
output field is singular.
"""

from datetime import date, datetime

from app.market_data.market_session import MarketSessionStatus
from app.trading.conditions.cooldown import is_cooldown_complete
from app.trading.conditions.expiry_day_filter import is_expiry_allowed
from app.trading.conditions.gap_filter import is_gap_filter_ok
from app.trading.conditions.liquidity import is_liquidity_ok
from app.trading.conditions.market_open_filter import is_market_open
from app.trading.conditions.models import NoTradeReason, TradingConditions
from app.trading.conditions.no_trade_zone_filter import is_within_no_trade_zone
from app.trading.conditions.opening_range_filter import is_opening_range_complete
from app.trading.conditions.position_guard import is_position_guard_ok
from app.trading.conditions.session_validation import is_session_valid
from app.trading.context.models import MarketContext


def build_trading_conditions(
    *,
    session_state: MarketSessionStatus,
    current_timestamp: datetime,
    market_context: MarketContext,
    market_open: str,
    market_close: str,
    opening_range_minutes: int = 15,
    no_trade_zone_minutes: int = 15,
    expiry_date: date | None = None,
    allow_expiry_day_trading: bool = True,
    gap_percent: float | None = None,
    max_gap_percent: float = 1.0,
    has_open_position: bool = False,
    last_trade_closed_at: datetime | None = None,
    cooldown_minutes: int = 5,
    volume: int | None = None,
    min_volume: int = 0,
) -> TradingConditions:
    session_valid = is_session_valid(session_state, current_timestamp)

    within_trading_window = is_market_open(session_state) and not is_within_no_trade_zone(
        current_timestamp, market_close, no_trade_zone_minutes, market_context
    )

    opening_range_complete = is_opening_range_complete(
        current_timestamp, market_open, opening_range_minutes
    )
    expiry_allowed = is_expiry_allowed(current_timestamp, expiry_date, allow_expiry_day_trading)
    position_guard_ok = is_position_guard_ok(has_open_position)
    cooldown_complete = is_cooldown_complete(
        current_timestamp, last_trade_closed_at, cooldown_minutes
    )
    gap_filter_ok = is_gap_filter_ok(gap_percent, max_gap_percent)
    liquidity_ok = is_liquidity_ok(volume, min_volume)

    reason = _first_failing_reason(
        session_valid=session_valid,
        within_trading_window=within_trading_window,
        opening_range_complete=opening_range_complete,
        expiry_allowed=expiry_allowed,
        position_guard_ok=position_guard_ok,
        cooldown_complete=cooldown_complete,
        gap_filter_ok=gap_filter_ok,
        liquidity_ok=liquidity_ok,
    )

    return TradingConditions(
        as_of=current_timestamp,
        can_trade=reason is None,
        no_trade_reason=reason,
        session_valid=session_valid,
        opening_range_complete=opening_range_complete,
        within_trading_window=within_trading_window,
        expiry_allowed=expiry_allowed,
        liquidity_ok=liquidity_ok,
        cooldown_complete=cooldown_complete,
        gap_filter_ok=gap_filter_ok,
        position_guard_ok=position_guard_ok,
    )


def _first_failing_reason(
    *,
    session_valid: bool,
    within_trading_window: bool,
    opening_range_complete: bool,
    expiry_allowed: bool,
    position_guard_ok: bool,
    cooldown_complete: bool,
    gap_filter_ok: bool,
    liquidity_ok: bool,
) -> NoTradeReason | None:
    if not session_valid:
        return NoTradeReason.SESSION_INVALID
    if not within_trading_window:
        return NoTradeReason.OUTSIDE_TRADING_WINDOW
    if not opening_range_complete:
        return NoTradeReason.WITHIN_OPENING_RANGE
    if not expiry_allowed:
        return NoTradeReason.EXPIRY_NOT_ALLOWED
    if not position_guard_ok:
        return NoTradeReason.POSITION_ALREADY_OPEN
    if not cooldown_complete:
        return NoTradeReason.COOLDOWN_ACTIVE
    if not gap_filter_ok:
        return NoTradeReason.GAP_TOO_LARGE
    if not liquidity_ok:
        return NoTradeReason.INSUFFICIENT_LIQUIDITY
    return None
