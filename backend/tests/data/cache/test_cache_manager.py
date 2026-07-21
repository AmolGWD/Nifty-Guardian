from datetime import datetime

from app.data.cache.cache_manager import CacheManager
from app.data.models import Dataset
from tests.data.helpers import make_clean_series, make_key


def test_dataset_cache_round_trips() -> None:
    cache = CacheManager()
    key = make_key()
    dataset = Dataset(key=key, candles=tuple(make_clean_series(3)))

    assert cache.get_dataset(key) is None

    cache.set_dataset(key, dataset)

    assert cache.get_dataset(key) == dataset


def test_query_cache_round_trips() -> None:
    cache = CacheManager()
    key = make_key()
    start, end = datetime(2026, 7, 21), datetime(2026, 7, 22)
    records = make_clean_series(3)

    assert cache.get_query(key, start, end) is None

    cache.set_query(key, start, end, records)

    assert cache.get_query(key, start, end) == records


def test_invalidate_dataset_clears_both_caches_for_that_key_only() -> None:
    cache = CacheManager()
    key_a = make_key(symbol="NIFTY")
    key_b = make_key(symbol="BANKNIFTY")
    start, end = datetime(2026, 7, 21), datetime(2026, 7, 22)

    dataset_a = Dataset(key=key_a, candles=tuple(make_clean_series(3)))
    dataset_b = Dataset(key=key_b, candles=tuple(make_clean_series(3)))
    cache.set_dataset(key_a, dataset_a)
    cache.set_dataset(key_b, dataset_b)
    cache.set_query(key_a, start, end, make_clean_series(3))
    cache.set_query(key_b, start, end, make_clean_series(3))

    cache.invalidate_dataset(key_a)

    assert cache.get_dataset(key_a) is None
    assert cache.get_query(key_a, start, end) is None
    assert cache.get_dataset(key_b) == dataset_b
    assert cache.get_query(key_b, start, end) is not None


def test_clear_empties_everything() -> None:
    cache = CacheManager()
    key = make_key()
    cache.set_dataset(key, Dataset(key=key, candles=tuple(make_clean_series(3))))
    cache.set_query(key, datetime(2026, 7, 21), datetime(2026, 7, 22), make_clean_series(3))

    cache.clear()

    assert cache.get_dataset(key) is None
    assert cache.get_query(key, datetime(2026, 7, 21), datetime(2026, 7, 22)) is None
