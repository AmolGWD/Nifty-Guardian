"""
Target calculation: ATR-based, same rationale as stop_loss.py - scales
with current volatility rather than an arbitrary fixed percentage.
"""

from app.trading.strategy.models import StrategyDirection


def calculate_target(
    entry_price: float, atr: float, atr_multiplier: float, direction: StrategyDirection
) -> float:
    distance = atr * atr_multiplier

    if direction == StrategyDirection.LONG:
        return entry_price + distance
    if direction == StrategyDirection.SHORT:
        return entry_price - distance
    return entry_price
