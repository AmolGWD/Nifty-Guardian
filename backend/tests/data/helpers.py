from datetime import datetime, timedelta

from app.data.models import DatasetKey, Exchange, Instrument, OHLCVRecord, Timeframe


def make_key(
    *,
    symbol: str = "NIFTY",
    exchange: Exchange = Exchange.NSE,
    timeframe: Timeframe = Timeframe.FIFTEEN_MINUTE,
) -> DatasetKey:
    return DatasetKey(symbol=symbol, exchange=exchange, timeframe=timeframe)


def make_instrument(
    *,
    symbol: str = "NIFTY",
    exchange: Exchange = Exchange.NSE,
    timeframe: Timeframe = Timeframe.FIFTEEN_MINUTE,
    name: str = "Nifty 50",
    lot_size: int = 50,
) -> Instrument:
    return Instrument(
        symbol=symbol, exchange=exchange, timeframe=timeframe, name=name, lot_size=lot_size
    )


def make_record(
    *,
    timestamp: datetime = datetime(2026, 7, 21, 9, 15),
    open: float = 100.0,
    high: float = 101.0,
    low: float = 99.0,
    close: float = 100.5,
    volume: int = 10_000,
) -> OHLCVRecord:
    return OHLCVRecord(
        timestamp=timestamp, open=open, high=high, low=low, close=close, volume=volume
    )


def make_clean_series(
    count: int = 10,
    *,
    start: datetime = datetime(2026, 7, 21, 9, 15),
    interval_minutes: int = 15,
) -> list[OHLCVRecord]:
    records = []
    timestamp = start
    close = 100.0
    for _ in range(count):
        open_price = close
        close = close + 1.0
        records.append(
            make_record(
                timestamp=timestamp,
                open=open_price,
                high=close + 1.0,
                low=open_price - 1.0,
                close=close,
                volume=10_000,
            )
        )
        timestamp += timedelta(minutes=interval_minutes)
    return records
