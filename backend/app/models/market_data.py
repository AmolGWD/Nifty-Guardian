from dataclasses import dataclass


@dataclass
class MarketData:
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