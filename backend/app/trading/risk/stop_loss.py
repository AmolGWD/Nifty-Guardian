"""
Stop-loss calculation: ATR-based, not a flat percentage of price - the
distance scales with how volatile the instrument currently is, rather
than an arbitrary fixed percentage.
"""

from app.trading.strategy.models import StrategyDirection


def calculate_stop_loss(
    entry_price: float, atr: float, atr_multiplier: float, direction: StrategyDirection
) -> float:
    distance = atr * atr_multiplier

    if direction == StrategyDirection.LONG:
        return entry_price - distance
    if direction == StrategyDirection.SHORT:
        return entry_price + distance
    return entry_price
