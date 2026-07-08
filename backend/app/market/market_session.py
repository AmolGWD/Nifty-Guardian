"""
========================================
 NIFTY Guardian Market Session
========================================
"""

from datetime import datetime

from app.config.settings import MARKET_OPEN
from app.config.settings import MARKET_CLOSE


def get_market_status() -> str:
    """
    Returns the current market session.
    """

    current_time = datetime.now().strftime("%H:%M")

    if current_time < MARKET_OPEN:
        return "🟡 Pre Market"

    if MARKET_OPEN <= current_time <= MARKET_CLOSE:
        return "🟢 Market Open"

    return "🔴 Market Closed"