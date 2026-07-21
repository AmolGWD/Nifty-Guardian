"""
In-memory repository for validated historical datasets. Each dataset's
candles are stored once, sorted by timestamp, alongside a parallel
tuple of just the timestamps - built once at import/replace/append
time, not on every query - so date-range queries can binary-search
(`bisect`) for their start/end bounds in O(log n) and copy out only
the matching slice, rather than scanning every candle on every call.
This is the concrete answer to "avoid loading unnecessary data into
memory" for datasets spanning several years of intraday candles.

`import_dataset`/`replace_dataset`/`append_dataset` all validate before
storing (via `app.data.validation.validator.validate_dataset`) and
raise `DatasetValidationError` (carrying the full `ValidationReport`)
when the result isn't valid - unless the caller explicitly passes
`force=True`. Data quality problems are surfaced by default, not
silently persisted, but a caller who has already reviewed a report can
still choose to store anyway.
"""

import bisect
from datetime import date, datetime

from app.data.models import (
    Dataset,
    DatasetKey,
    DatasetStatistics,
    Instrument,
    OHLCVRecord,
    ValidationReport,
)
from app.data.validation.validator import validate_dataset


class DatasetValidationError(Exception):
    def __init__(self, report: ValidationReport) -> None:
        self.report = report
        super().__init__(
            f"Dataset {report.key.symbol}/{report.key.exchange}/{report.key.timeframe} "
            f"failed validation with {len(report.issues)} issue(s)"
        )


class HistoricalDataRepository:
    def __init__(self) -> None:
        self._datasets: dict[DatasetKey, Dataset] = {}
        self._timestamps: dict[DatasetKey, tuple[datetime, ...]] = {}
        self._instruments: dict[DatasetKey, Instrument] = {}

    def register_instrument(self, instrument: Instrument) -> None:
        key = DatasetKey(
            symbol=instrument.symbol, exchange=instrument.exchange, timeframe=instrument.timeframe
        )
        self._instruments[key] = instrument

    def import_dataset(
        self, key: DatasetKey, candles: list[OHLCVRecord], *, force: bool = False
    ) -> ValidationReport:
        return self._store(key, candles, force=force)

    def replace_dataset(
        self, key: DatasetKey, candles: list[OHLCVRecord], *, force: bool = False
    ) -> ValidationReport:
        return self._store(key, candles, force=force)

    def append_dataset(
        self, key: DatasetKey, candles: list[OHLCVRecord], *, force: bool = False
    ) -> ValidationReport:
        existing = self._datasets.get(key)
        combined = list(existing.candles) + candles if existing is not None else list(candles)
        return self._store(key, combined, force=force)

    def _store(
        self, key: DatasetKey, candles: list[OHLCVRecord], *, force: bool
    ) -> ValidationReport:
        report = validate_dataset(key, candles, key.timeframe)
        if not report.is_valid and not force:
            raise DatasetValidationError(report)

        sorted_candles = tuple(sorted(candles, key=lambda candle: candle.timestamp))
        self._datasets[key] = Dataset(key=key, candles=sorted_candles)
        self._timestamps[key] = tuple(candle.timestamp for candle in sorted_candles)
        return report

    def query_date_range(
        self, key: DatasetKey, start: datetime, end: datetime
    ) -> list[OHLCVRecord]:
        dataset = self._datasets.get(key)
        timestamps = self._timestamps.get(key)
        if dataset is None or timestamps is None:
            return []

        left = bisect.bisect_left(timestamps, start)
        right = bisect.bisect_right(timestamps, end)
        return list(dataset.candles[left:right])

    def query_single_day(self, key: DatasetKey, day: date) -> list[OHLCVRecord]:
        start = datetime.combine(day, datetime.min.time())
        end = datetime.combine(day, datetime.max.time())
        return self.query_date_range(key, start, end)

    def query_latest_candle(self, key: DatasetKey) -> OHLCVRecord | None:
        dataset = self._datasets.get(key)
        if dataset is None or not dataset.candles:
            return None
        return dataset.candles[-1]

    def query_instrument(self, key: DatasetKey) -> Dataset | None:
        return self._datasets.get(key)

    def get_instrument_metadata(self, key: DatasetKey) -> Instrument | None:
        return self._instruments.get(key)

    def list_instruments(self) -> list[DatasetKey]:
        return list(self._datasets.keys())

    def dataset_statistics(self, key: DatasetKey) -> DatasetStatistics | None:
        dataset = self._datasets.get(key)
        if dataset is None:
            return None

        if not dataset.candles:
            return DatasetStatistics(
                key=key,
                candle_count=0,
                first_timestamp=None,
                last_timestamp=None,
                min_close=None,
                max_close=None,
                average_volume=None,
            )

        closes = [candle.close for candle in dataset.candles]
        volumes = [candle.volume for candle in dataset.candles]

        return DatasetStatistics(
            key=key,
            candle_count=len(dataset.candles),
            first_timestamp=dataset.candles[0].timestamp,
            last_timestamp=dataset.candles[-1].timestamp,
            min_close=min(closes),
            max_close=max(closes),
            average_volume=sum(volumes) / len(volumes),
        )
