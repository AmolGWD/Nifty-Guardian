"""
Historical Data Platform domain models - frozen, same discipline as
the rest of the application (ADR-0006).

`OHLCVRecord` is deliberately a new model, not a reuse of
`app.market_data.schemas.Candle` (which is frozen and cannot gain new
fields this phase): `app.market_data` is the live, Kite-facing layer,
while `app.data` is this platform's own historical storage/query
representation, and needs room the former doesn't - `open_interest`
plus a generic `metadata` slot, future-ready for PCR and option Greeks
without inventing precise field names for data this phase doesn't
carry yet.

Collections stored inside frozen models use `tuple`, not `list` -
`ConfigDict(frozen=True)` only stops *reassigning* an attribute, it
does not stop mutating a mutable object already referenced by one
(a `list` field could still be `.append()`-ed to from outside). A
`Dataset`'s candles are the platform's actual stored data, so this
needed to be genuinely immutable, not merely frozen-looking.
"""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict


class Exchange(StrEnum):
    NSE = "NSE"
    BSE = "BSE"


class Timeframe(StrEnum):
    ONE_MINUTE = "1minute"
    THREE_MINUTE = "3minute"
    FIVE_MINUTE = "5minute"
    FIFTEEN_MINUTE = "15minute"
    THIRTY_MINUTE = "30minute"
    ONE_HOUR = "60minute"
    ONE_DAY = "day"


class DatasetKey(BaseModel):
    model_config = ConfigDict(frozen=True)

    symbol: str
    exchange: Exchange
    timeframe: Timeframe


class Instrument(BaseModel):
    model_config = ConfigDict(frozen=True)

    symbol: str
    exchange: Exchange
    timeframe: Timeframe
    name: str = ""
    lot_size: int = 1
    tick_size: float = 0.05


class OHLCVRecord(BaseModel):
    model_config = ConfigDict(frozen=True)

    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int

    open_interest: int | None = None
    metadata: dict[str, float] | None = None


class Dataset(BaseModel):
    model_config = ConfigDict(frozen=True)

    key: DatasetKey
    candles: tuple[OHLCVRecord, ...]


class DatasetStatistics(BaseModel):
    model_config = ConfigDict(frozen=True)

    key: DatasetKey
    candle_count: int
    first_timestamp: datetime | None
    last_timestamp: datetime | None
    min_close: float | None
    max_close: float | None
    average_volume: float | None


class ValidationIssueType(StrEnum):
    MISSING_CANDLE = "MissingCandle"
    DUPLICATE_TIMESTAMP = "DuplicateTimestamp"
    OUT_OF_ORDER = "OutOfOrder"
    NEGATIVE_PRICE = "NegativePrice"
    NEGATIVE_VOLUME = "NegativeVolume"
    HIGH_BELOW_OPEN_OR_CLOSE = "HighBelowOpenOrClose"
    LOW_ABOVE_OPEN_OR_CLOSE = "LowAboveOpenOrClose"
    TIMEZONE_INCONSISTENT = "TimezoneInconsistent"
    ABNORMAL_PRICE_MOVE = "AbnormalPriceMove"
    ABNORMAL_VOLUME = "AbnormalVolume"


class ValidationIssue(BaseModel):
    model_config = ConfigDict(frozen=True)

    issue_type: ValidationIssueType
    timestamp: datetime | None
    detail: str


class ValidationReport(BaseModel):
    model_config = ConfigDict(frozen=True)

    key: DatasetKey
    total_candles: int
    issues: tuple[ValidationIssue, ...]

    @property
    def is_valid(self) -> bool:
        return len(self.issues) == 0
