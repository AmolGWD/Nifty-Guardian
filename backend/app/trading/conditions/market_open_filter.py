"""
Market open filter - one half of `within_trading_window`, combined
with the no-trade-zone filter.
"""

from app.market_data.market_session import MarketSessionStatus


def is_market_open(session_state: MarketSessionStatus) -> bool:
    return session_state == MarketSessionStatus.OPEN
