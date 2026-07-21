from datetime import datetime

from app.data.cache.cache_manager import CacheManager
from app.data.repository import HistoricalDataRepository
from app.data.services.query_service import QueryService
from tests.data.helpers import make_clean_series, make_instrument, make_key


def test_get_date_range_delegates_to_repository() -> None:
    repo = HistoricalDataRepository()
    key = make_key()
    repo.import_dataset(key, make_clean_series(10, start=datetime(2026, 7, 21, 9, 15)))
    service = QueryService(repo)

    result = service.get_date_range(
        key, datetime(2026, 7, 21, 9, 15), datetime(2026, 7, 21, 9, 45)
    )

    assert len(result) == 3


def test_get_date_range_uses_the_cache_on_repeat_calls() -> None:
    repo = HistoricalDataRepository()
    key = make_key()
    repo.import_dataset(key, make_clean_series(10, start=datetime(2026, 7, 21, 9, 15)))
    cache = CacheManager()
    service = QueryService(repo, cache)
    start, end = datetime(2026, 7, 21, 9, 15), datetime(2026, 7, 21, 9, 45)

    first = service.get_date_range(key, start, end)
    assert cache.get_query(key, start, end) == first

    # mutate the repository directly - a cached second call must still
    # return the original (now stale) cached result, proving it came
    # from cache rather than being recomputed
    repo.replace_dataset(key, make_clean_series(2, start=datetime(2030, 1, 1)))
    second = service.get_date_range(key, start, end)

    assert second == first


def test_get_single_day_filters_by_calendar_date() -> None:
    repo = HistoricalDataRepository()
    key = make_key()
    day_one = make_clean_series(5, start=datetime(2026, 7, 21, 9, 15))
    day_two = make_clean_series(5, start=datetime(2026, 7, 22, 9, 15))
    repo.import_dataset(key, day_one + day_two)
    service = QueryService(repo)

    result = service.get_single_day(key, datetime(2026, 7, 22).date())

    assert len(result) == 5


def test_get_latest_candle_delegates_to_repository() -> None:
    repo = HistoricalDataRepository()
    key = make_key()
    candles = make_clean_series(5)
    repo.import_dataset(key, candles)
    service = QueryService(repo)

    assert service.get_latest_candle(key) is not None
    assert service.get_latest_candle(key).timestamp == candles[-1].timestamp  # type: ignore[union-attr]


def test_get_instrument_metadata_and_list_instruments() -> None:
    repo = HistoricalDataRepository()
    instrument = make_instrument()
    repo.register_instrument(instrument)
    repo.import_dataset(make_key(), make_clean_series(3))
    service = QueryService(repo)

    assert service.get_instrument_metadata(make_key()) == instrument
    assert make_key() in service.list_instruments()


def test_get_statistics_delegates_to_repository() -> None:
    repo = HistoricalDataRepository()
    key = make_key()
    repo.import_dataset(key, make_clean_series(5))
    service = QueryService(repo)

    stats = service.get_statistics(key)

    assert stats is not None
    assert stats.candle_count == 5
