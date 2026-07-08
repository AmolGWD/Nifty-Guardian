"""
========================================
 NIFTY Guardian Market Data Model
========================================
"""

from dataclasses import dataclass


@dataclass
class MarketData:
    """
    Holds all market information required
    by the strategy engine.
    """

    current_price: float
    previous_close: float
    open_price: float

    ema: float
    rsi: float

    supertrend_green: bool

    resistance: float
    support: float

    ce_oi: int
    pe_oi: int

    volume: int = 0

    high: float = 0
    low: float = 0

    atr: float = 0

    vwap: float = 0