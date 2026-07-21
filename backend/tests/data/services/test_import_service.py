from datetime import datetime

from app.data.cache.cache_manager import CacheManager
from app.data.models import Dataset, OHLCVRecord
from app.data.repository import HistoricalDataRepository
from app.data.services.import_service import ImportService
from tests.data.helpers import make_clean_series, make_instrument, make_key


class _FakeProvider:
    def __init__(self, records: list[OHLCVRecord]) -> None:
        self._records = records

    def fetch(self, start: datetime, end: datetime) -> list[OHLCVRecord]:
        return [r for r in self._records if start <= r.timestamp <= end]


def test_import_from_provider_stores_data_and_registers_instrument() -> None:
    repo = HistoricalDataRepository()
    service = ImportService(repo)
    instrument = make_instrument()
    provider = _FakeProvider(make_clean_series(5))

    report = service.import_from_provider(
        provider, instrument, datetime(2026, 1, 1), datetime(2026, 12, 31)
    )

    assert report.is_valid is True
    key = make_key()
    assert repo.query_instrument(key) is not None
    assert repo.get_instrument_metadata(key) == instrument


def test_import_from_provider_invalidates_cache() -> None:
    repo = HistoricalDataRepository()
    cache = CacheManager()
    key = make_key()
    cache.set_dataset(key, Dataset(key=key, candles=tuple(make_clean_series(3))))

    service = ImportService(repo, cache)
    provider = _FakeProvider(make_clean_series(5))

    service.import_from_provider(
        provider, make_instrument(), datetime(2026, 1, 1), datetime(2026, 12, 31)
    )

    assert cache.get_dataset(key) is None


def test_append_adds_to_existing_dataset() -> None:
    repo = HistoricalDataRepository()
    service = ImportService(repo)
    instrument = make_instrument()

    service.append(instrument, make_clean_series(5, start=datetime(2026, 7, 21, 9, 15)))
    service.append(instrument, make_clean_series(5, start=datetime(2026, 7, 21, 10, 30)))

    key = make_key()
    dataset = repo.query_instrument(key)
    assert dataset is not None
    assert len(dataset.candles) == 10
