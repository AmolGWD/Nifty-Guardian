"""
Normalized, validated market data shapes.

The rest of the application works with these, never with raw Kite SDK
dicts - normalization happens once, at the boundary in this package.
"""

from datetime import date, datetime

from pydantic import BaseModel


class SpotPrice(BaseModel):
    symbol: str
    price: float
    as_of: datetime


class Candle(BaseModel):
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int


class Instrument(BaseModel):
    instrument_token: int
    trading_symbol: str
    name: str
    expiry: date | None
    strike: float
    instrument_type: str
    lot_size: int


class OptionContract(BaseModel):
    instrument: Instrument
    last_price: float
