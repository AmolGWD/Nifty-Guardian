from datetime import datetime

import pytest

from app.data.repository import DatasetValidationError, HistoricalDataRepository
from tests.data.helpers import make_clean_series, make_instrument, make_key, make_record


def test_import_dataset_stores_valid_data() -> None:
    repo = HistoricalDataRepository()
    key = make_key()
    candles = make_clean_series(5)

    report = repo.import_dataset(key, candles)

    assert report.is_valid is True
    assert repo.query_instrument(key) is not None
    assert len(repo.query_instrument(key).candles) == 5  # type: ignore[union-attr]


def test_import_dataset_sorts_out_of_order_input() -> None:
    repo = HistoricalDataRepository()
    key = make_key()
    candles = list(reversed(make_clean_series(5)))

    repo.import_dataset(key, candles, force=True)

    stored = repo.query_instrument(key)
    assert stored is not None
    timestamps = [c.timestamp for c in stored.candles]
    assert timestamps == sorted(timestamps)


def test_import_dataset_raises_on_invalid_data_by_default() -> None:
    repo = HistoricalDataRepository()
    key = make_key()
    candles = [make_record(open=-5.0)]

    with pytest.raises(DatasetValidationError) as exc_info:
        repo.import_dataset(key, candles)

    assert len(exc_info.value.report.issues) > 0


def test_import_dataset_stores_anyway_when_forced() -> None:
    repo = HistoricalDataRepository()
    key = make_key()
    candles = [make_record(open=-5.0)]

    report = repo.import_dataset(key, candles, force=True)

    assert report.is_valid is False
    assert repo.query_instrument(key) is not None


def test_append_dataset_combines_with_existing_data() -> None:
    repo = HistoricalDataRepository()
    key = make_key()
    first_batch = make_clean_series(5, start=datetime(2026, 7, 21, 9, 15))
    second_batch = make_clean_series(
        5, start=datetime(2026, 7, 21, 10, 30)
    )  # continues after first batch

    repo.import_dataset(key, first_batch)
    repo.append_dataset(key, second_batch)

    stored = repo.query_instrument(key)
    assert stored is not None
    assert len(stored.candles) == 10


def test_replace_dataset_overwrites_existing_data() -> None:
    repo = HistoricalDataRepository()
    key = make_key()
    repo.import_dataset(key, make_clean_series(5))

    new_candles = make_clean_series(3, start=datetime(2027, 1, 1, 9, 15))
    repo.replace_dataset(key, new_candles)

    stored = repo.query_instrument(key)
    assert stored is not None
    assert len(stored.candles) == 3


def test_query_date_range_returns_only_matching_candles() -> None:
    repo = HistoricalDataRepository()
    key = make_key()
    candles = make_clean_series(10, start=datetime(2026, 7, 21, 9, 15))
    repo.import_dataset(key, candles)

    result = repo.query_date_range(
        key, datetime(2026, 7, 21, 9, 30), datetime(2026, 7, 21, 10, 0)
    )

    assert [c.timestamp for c in result] == [
        datetime(2026, 7, 21, 9, 30),
        datetime(2026, 7, 21, 9, 45),
        datetime(2026, 7, 21, 10, 0),
    ]


def test_query_date_range_returns_empty_for_unknown_key() -> None:
    repo = HistoricalDataRepository()
    assert repo.query_date_range(make_key(), datetime(2026, 1, 1), datetime(2026, 1, 2)) == []


def test_query_single_day_filters_to_that_calendar_date() -> None:
    repo = HistoricalDataRepository()
    key = make_key()
    day_one = make_clean_series(5, start=datetime(2026, 7, 21, 9, 15))
    day_two = make_clean_series(5, start=datetime(2026, 7, 22, 9, 15))
    repo.import_dataset(key, day_one + day_two)

    result = repo.query_single_day(key, datetime(2026, 7, 22).date())

    assert len(result) == 5
    assert all(c.timestamp.date() == datetime(2026, 7, 22).date() for c in result)


def test_query_latest_candle_returns_the_last_one() -> None:
    repo = HistoricalDataRepository()
    key = make_key()
    candles = make_clean_series(5)
    repo.import_dataset(key, candles)

    latest = repo.query_latest_candle(key)

    assert latest is not None
    assert latest.timestamp == candles[-1].timestamp


def test_query_latest_candle_is_none_for_unknown_key() -> None:
    repo = HistoricalDataRepository()
    assert repo.query_latest_candle(make_key()) is None


def test_instrument_metadata_round_trips() -> None:
    repo = HistoricalDataRepository()
    instrument = make_instrument()
    repo.register_instrument(instrument)

    fetched = repo.get_instrument_metadata(make_key())

    assert fetched == instrument


def test_list_instruments_returns_every_stored_key() -> None:
    repo = HistoricalDataRepository()
    key_a = make_key(symbol="NIFTY")
    key_b = make_key(symbol="BANKNIFTY")
    repo.import_dataset(key_a, make_clean_series(3))
    repo.import_dataset(key_b, make_clean_series(3))

    keys = repo.list_instruments()

    assert set(keys) == {key_a, key_b}


def test_dataset_statistics_matches_hand_calculated_values() -> None:
    repo = HistoricalDataRepository()
    key = make_key()
    candles = [
        make_record(timestamp=datetime(2026, 7, 21, 9, 15), close=100.0, volume=1000),
        make_record(timestamp=datetime(2026, 7, 21, 9, 30), close=110.0, volume=2000),
        make_record(timestamp=datetime(2026, 7, 21, 9, 45), close=90.0, volume=3000),
    ]
    repo.import_dataset(key, candles, force=True)

    stats = repo.dataset_statistics(key)

    assert stats is not None
    assert stats.candle_count == 3
    assert stats.min_close == 90.0
    assert stats.max_close == 110.0
    assert stats.average_volume == 2000.0
    assert stats.first_timestamp == datetime(2026, 7, 21, 9, 15)
    assert stats.last_timestamp == datetime(2026, 7, 21, 9, 45)


def test_dataset_statistics_is_none_for_unknown_key() -> None:
    repo = HistoricalDataRepository()
    assert repo.dataset_statistics(make_key()) is None
