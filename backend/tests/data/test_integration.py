"""
End-to-end: CSV provider -> ImportService -> repository (validate +
store) -> QueryService (cached range query) -> statistics, exercising
every layer of the platform together rather than each in isolation.
"""

from datetime import datetime
from pathlib import Path

from app.data.cache.cache_manager import CacheManager
from app.data.providers.csv_provider import CSVHistoricalDataProvider
from app.data.repository import HistoricalDataRepository
from app.data.services.import_service import ImportService
from app.data.services.query_service import QueryService
from tests.data.helpers import make_instrument, make_key

_FIXTURE_PATH = Path(__file__).parent / "providers" / "fixtures" / "sample.csv"


def test_full_platform_flow_from_csv_to_query_and_statistics() -> None:
    repository = HistoricalDataRepository()
    cache = CacheManager()
    import_service = ImportService(repository, cache)
    query_service = QueryService(repository, cache)

    provider = CSVHistoricalDataProvider(_FIXTURE_PATH)
    instrument = make_instrument()

    report = import_service.import_from_provider(
        provider, instrument, datetime(2026, 1, 1), datetime(2026, 12, 31)
    )
    assert report.is_valid is True

    key = make_key()
    result = query_service.get_date_range(
        key, datetime(2026, 7, 21, 9, 15), datetime(2026, 7, 21, 9, 30)
    )
    assert len(result) == 2

    stats = query_service.get_statistics(key)
    assert stats is not None
    assert stats.candle_count == 3

    metadata = query_service.get_instrument_metadata(key)
    assert metadata == instrument

    latest = query_service.get_latest_candle(key)
    assert latest is not None
    assert latest.timestamp == datetime(2026, 7, 21, 9, 45)
