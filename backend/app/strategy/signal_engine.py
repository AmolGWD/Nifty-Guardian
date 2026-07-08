"""
========================================
 NIFTY Guardian Strategy Engine
========================================
"""

from app.config.settings import (
    BREAKOUT_SCORE,
    EMA_SCORE,
    MIN_CONFIDENCE,
    OI_SCORE,
    RISK_REWARD,
    RSI_BUY,
    RSI_SCORE,
    STOPLOSS_BUFFER,
    SUPERTREND_SCORE,
)

from app.models.market_data import MarketData
from app.models.signal import Signal


def generate_signal(data: MarketData) -> Signal:

    confidence = 0
    reasons = []

    # --------------------------
    # EMA
    # --------------------------

    if data.current_price > data.ema:
        confidence += EMA_SCORE
        reasons.append("EMA Confirmed")
    else:
        reasons.append("EMA Failed")

    # --------------------------
    # Supertrend
    # --------------------------

    if data.supertrend_green:
        confidence += SUPERTREND_SCORE
        reasons.append("Supertrend Green")
    else:
        reasons.append("Supertrend Red")

    # --------------------------
    # RSI
    # --------------------------

    if data.rsi > RSI_BUY:
        confidence += RSI_SCORE
        reasons.append("RSI Above 55")
    else:
        reasons.append("RSI Below 55")

    # --------------------------
    # Resistance Break
    # --------------------------

    if data.current_price > data.resistance:
        confidence += BREAKOUT_SCORE
        reasons.append("Resistance Break")
    else:
        reasons.append("No Resistance Break")

    # --------------------------
    # Option Chain
    # --------------------------

    if data.pe_oi > data.ce_oi:
        confidence += OI_SCORE
        reasons.append("OI Confirmed")
    else:
        reasons.append("OI Not Confirmed")

    # --------------------------
    # Entry & Targets
    # --------------------------

    if confidence >= MIN_CONFIDENCE:

        entry = data.current_price

        stop_loss = data.support - STOPLOSS_BUFFER

        risk = entry - stop_loss

        target1 = entry + risk

        target2 = entry + (risk * RISK_REWARD)

        return Signal(
            action="BUY CE",
            confidence=confidence,
            reasons=reasons,
            entry=entry,
            stop_loss=stop_loss,
            target1=target1,
            target2=target2,
            market_bias="Bullish",
        )

    return Signal(
        action="NO TRADE",
        confidence=confidence,
        reasons=reasons,
        market_bias="Neutral",
    )