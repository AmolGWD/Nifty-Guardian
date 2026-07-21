"""
In-memory cache for the Historical Data Platform: whole datasets and
individual date-range query results, both invalidated per-key rather
than only by a global clear - importing new data for one instrument
must not force every other cached instrument to be recomputed.
"""

from datetime import datetime

from app.data.models import Dataset, DatasetKey, OHLCVRecord

_QueryCacheKey = tuple[DatasetKey, datetime, datetime]


class CacheManager:
    def __init__(self) -> None:
        self._dataset_cache: dict[DatasetKey, Dataset] = {}
        self._query_cache: dict[_QueryCacheKey, list[OHLCVRecord]] = {}

    def get_dataset(self, key: DatasetKey) -> Dataset | None:
        return self._dataset_cache.get(key)

    def set_dataset(self, key: DatasetKey, dataset: Dataset) -> None:
        self._dataset_cache[key] = dataset

    def get_query(
        self, key: DatasetKey, start: datetime, end: datetime
    ) -> list[OHLCVRecord] | None:
        return self._query_cache.get((key, start, end))

    def set_query(
        self, key: DatasetKey, start: datetime, end: datetime, result: list[OHLCVRecord]
    ) -> None:
        self._query_cache[(key, start, end)] = result

    def invalidate_dataset(self, key: DatasetKey) -> None:
        self._dataset_cache.pop(key, None)
        stale_query_keys = [query_key for query_key in self._query_cache if query_key[0] == key]
        for query_key in stale_query_keys:
            del self._query_cache[query_key]

    def clear(self) -> None:
        self._dataset_cache.clear()
        self._query_cache.clear()
