from datetime import datetime

from app.validation.models import Window, WindowConfig, WindowType
from app.validation.window_generator import generate_windows

_DATA_START = datetime(2026, 1, 1)
_DATA_END = datetime(2026, 1, 10)


def _config(window_type: WindowType) -> WindowConfig:
    return WindowConfig(
        window_type=window_type,
        training_duration_days=2,
        testing_duration_days=1,
        step_size_days=1,
        minimum_candles=0,
        minimum_trades=0,
    )


def _generate(window_type: WindowType, *, data_end: datetime = _DATA_END) -> tuple[Window, ...]:
    return generate_windows(_config(window_type), data_start=_DATA_START, data_end=data_end)


def test_rolling_window_train_duration_stays_constant() -> None:
    windows = _generate(WindowType.ROLLING)

    assert len(windows) == 7
    for window in windows:
        assert (window.train_end - window.train_start).days == 2
        assert (window.test_end - window.test_start).days == 1


def test_rolling_window_both_train_and_test_slide_forward() -> None:
    windows = _generate(WindowType.ROLLING)

    assert windows[0].train_start == datetime(2026, 1, 1)
    assert windows[1].train_start == datetime(2026, 1, 2)
    assert windows[0].test_start == datetime(2026, 1, 3)
    assert windows[1].test_start == datetime(2026, 1, 4)


def test_expanding_window_train_start_stays_fixed() -> None:
    windows = _generate(WindowType.EXPANDING)

    assert all(window.train_start == _DATA_START for window in windows)


def test_expanding_window_train_end_grows_each_iteration() -> None:
    windows = _generate(WindowType.EXPANDING)

    train_ends = [window.train_end for window in windows]
    assert train_ends == sorted(train_ends)
    assert len(set(train_ends)) == len(train_ends)


def test_anchored_window_train_never_changes() -> None:
    windows = _generate(WindowType.ANCHORED)

    first_train = (windows[0].train_start, windows[0].train_end)
    assert all((window.train_start, window.train_end) == first_train for window in windows)


def test_anchored_window_test_slides_forward() -> None:
    windows = _generate(WindowType.ANCHORED)

    test_starts = [window.test_start for window in windows]
    assert test_starts == sorted(test_starts)
    assert len(set(test_starts)) == len(test_starts)


def test_no_partial_final_window_is_produced() -> None:
    windows = _generate(WindowType.ROLLING)

    assert all(window.test_end <= _DATA_END for window in windows)


def test_window_indices_are_sequential_from_zero() -> None:
    windows = _generate(WindowType.ROLLING)

    assert [window.window_index for window in windows] == list(range(len(windows)))


def test_no_windows_when_data_is_too_short() -> None:
    windows = generate_windows(
        _config(WindowType.ROLLING), data_start=_DATA_START, data_end=datetime(2026, 1, 2)
    )

    assert windows == ()


def test_generation_is_deterministic() -> None:
    config = _config(WindowType.ROLLING)

    first = generate_windows(config, data_start=_DATA_START, data_end=_DATA_END)
    second = generate_windows(config, data_start=_DATA_START, data_end=_DATA_END)

    assert first == second
