from pathlib import Path

from app.runtime.market_data_source import HistoricalReplaySource, StaticListSource
from tests.runtime.helpers import build_candles


def test_static_list_source_iterates_all_candles() -> None:
    candles = build_candles(5)
    source = StaticListSource(candles)
    assert len(source) == 5
    assert list(source) == candles


def test_static_list_source_respects_maximum_candles() -> None:
    candles = build_candles(10)
    source = StaticListSource(candles, maximum_candles=3)
    assert len(source) == 3
    assert list(source) == candles[:3]


def test_static_list_source_can_be_iterated_more_than_once() -> None:
    source = StaticListSource(build_candles(3))
    first_pass = list(source)
    second_pass = list(source)
    assert first_pass == second_pass


def test_historical_replay_source_loads_from_csv(tmp_path: Path) -> None:
    csv_path = tmp_path / "candles.csv"
    csv_path.write_text(
        "timestamp,open,high,low,close,volume\n"
        "2026-01-05 09:15:00,100,101,99,100.5,10000\n"
        "2026-01-05 09:30:00,100.5,102,100,101.5,11000\n"
    )
    source = HistoricalReplaySource(str(csv_path))
    assert len(source) == 2
    candles = list(source)
    assert candles[0].close == 100.5
    assert candles[1].close == 101.5


def test_historical_replay_source_respects_maximum_candles(tmp_path: Path) -> None:
    csv_path = tmp_path / "candles.csv"
    csv_path.write_text(
        "timestamp,open,high,low,close,volume\n"
        "2026-01-05 09:15:00,100,101,99,100.5,10000\n"
        "2026-01-05 09:30:00,100.5,102,100,101.5,11000\n"
        "2026-01-05 09:45:00,101.5,103,101,102.5,12000\n"
    )
    source = HistoricalReplaySource(str(csv_path), maximum_candles=2)
    assert len(source) == 2
