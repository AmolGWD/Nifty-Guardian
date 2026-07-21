from datetime import datetime
from pathlib import Path

from app.data.providers.csv_provider import CSVHistoricalDataProvider

_FIXTURE_PATH = Path(__file__).parent / "fixtures" / "sample.csv"


def test_fetch_returns_all_records_within_range() -> None:
    provider = CSVHistoricalDataProvider(_FIXTURE_PATH)

    records = provider.fetch(datetime(2026, 7, 21, 0, 0), datetime(2026, 7, 22, 0, 0))

    assert len(records) == 3
    assert records[0].close == 101.0


def test_fetch_filters_out_of_range_records() -> None:
    provider = CSVHistoricalDataProvider(_FIXTURE_PATH)

    records = provider.fetch(datetime(2026, 7, 21, 9, 20), datetime(2026, 7, 21, 9, 40))

    assert len(records) == 1
    assert records[0].timestamp == datetime(2026, 7, 21, 9, 30)


def test_fetch_returns_empty_list_when_range_matches_nothing() -> None:
    provider = CSVHistoricalDataProvider(_FIXTURE_PATH)

    records = provider.fetch(datetime(2099, 1, 1), datetime(2099, 1, 2))

    assert records == []
