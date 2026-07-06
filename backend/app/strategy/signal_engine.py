from app.models.market_data import MarketData
from app.models.signal import Signal
from app.config.settings import EMA_SCORE


def generate_signal(data: MarketData):

    # Rule 1: Price must be above EMA
    if data.current_price <= data.ema:
        return Signal(
            action="NO TRADE",
            confidence=0,
            reasons=[
    "Price is below EMA ❌"
],
            entry=0,
            stop_loss=0,
            target1=0,
            target2=0,
        )

    # Passed EMA rule
    return Signal(
    action="WAIT",
    confidence=EMA_SCORE,
    reasons=[
        "EMA Confirmed ✅"
    ],
    entry=0,
    stop_loss=0,
    target1=0,
    target2=0,
)