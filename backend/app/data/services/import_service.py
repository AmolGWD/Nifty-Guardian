"""
Imports historical data from any HistoricalDataProvider into the
repository, registering the instrument's metadata alongside it and
invalidating any cached copy of that dataset - a stale cache entry
surviving a re-import would silently serve old data forever otherwise.
"""

from datetime import datetime

from app.data.cache.cache_manager import CacheManager
from app.data.models import DatasetKey, Instrument, OHLCVRecord, ValidationReport
from app.data.providers.provider_interface import HistoricalDataProvider
from app.data.repository import HistoricalDataRepository


class ImportService:
    def __init__(
        self, repository: HistoricalDataRepository, cache: CacheManager | None = None
    ) -> None:
        self._repository = repository
        self._cache = cache

    def import_from_provider(
        self,
        provider: HistoricalDataProvider,
        instrument: Instrument,
        start: datetime,
        end: datetime,
        *,
        force: bool = False,
    ) -> ValidationReport:
        key = DatasetKey(
            symbol=instrument.symbol, exchange=instrument.exchange, timeframe=instrument.timeframe
        )
        candles = provider.fetch(start, end)
        return self._import(key, instrument, candles, replace=True, force=force)

    def append(
        self, instrument: Instrument, candles: list[OHLCVRecord], *, force: bool = False
    ) -> ValidationReport:
        key = DatasetKey(
            symbol=instrument.symbol, exchange=instrument.exchange, timeframe=instrument.timeframe
        )
        return self._import(key, instrument, candles, replace=False, force=force)

    def _import(
        self,
        key: DatasetKey,
        instrument: Instrument,
        candles: list[OHLCVRecord],
        *,
        replace: bool,
        force: bool,
    ) -> ValidationReport:
        if replace:
            report = self._repository.replace_dataset(key, candles, force=force)
        else:
            report = self._repository.append_dataset(key, candles, force=force)

        self._repository.register_instrument(instrument)

        if self._cache is not None:
            self._cache.invalidate_dataset(key)

        return report
