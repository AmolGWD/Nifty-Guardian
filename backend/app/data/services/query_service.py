"""
Read-only access to stored datasets, transparently caching date-range
query results (`CacheManager`) so a repeated query over the same
range/instrument doesn't re-slice the underlying dataset. Point lookups
(latest candle, instrument metadata, dataset list/statistics) are
already O(1)/O(log n) against the repository and aren't cached - the
overhead of a cache lookup wouldn't be worth it for those.
"""

from datetime import date, datetime

from app.data.cache.cache_manager import CacheManager
from app.data.models import DatasetKey, DatasetStatistics, Instrument, OHLCVRecord
from app.data.repository import HistoricalDataRepository


class QueryService:
    def __init__(
        self, repository: HistoricalDataRepository, cache: CacheManager | None = None
    ) -> None:
        self._repository = repository
        self._cache = cache

    def get_date_range(self, key: DatasetKey, start: datetime, end: datetime) -> list[OHLCVRecord]:
        if self._cache is not None:
            cached = self._cache.get_query(key, start, end)
            if cached is not None:
                return cached

        result = self._repository.query_date_range(key, start, end)

        if self._cache is not None:
            self._cache.set_query(key, start, end, result)

        return result

    def get_single_day(self, key: DatasetKey, day: date) -> list[OHLCVRecord]:
        return self._repository.query_single_day(key, day)

    def get_latest_candle(self, key: DatasetKey) -> OHLCVRecord | None:
        return self._repository.query_latest_candle(key)

    def get_instrument_metadata(self, key: DatasetKey) -> Instrument | None:
        return self._repository.get_instrument_metadata(key)

    def list_instruments(self) -> list[DatasetKey]:
        return self._repository.list_instruments()

    def get_statistics(self, key: DatasetKey) -> DatasetStatistics | None:
        return self._repository.dataset_statistics(key)
