"""
Deterministic train/test window generation for Walk-Forward Validation.
No randomization - the same `WindowConfig` and data range always
produce the same windows in the same order.

Three window types (see docs/VALIDATION_GUIDE.md for the full
rationale and worked examples):

- Rolling: both train_start and test dates slide forward by
  `step_size_days` each iteration; train duration stays constant.
- Expanding: train_start stays fixed at the data's own start; train_end
  (and therefore train duration) grows by `step_size_days` each
  iteration.
- Anchored: train_start and train_end are fixed after the first window
  (trained once); only the test window slides forward by
  `step_size_days` each iteration.

Generation stops as soon as a window's test_end would exceed the
available data - a partial, cut-off final window is never produced.
"""

from datetime import datetime, timedelta

from app.validation.models import Window, WindowConfig, WindowType


def generate_windows(
    config: WindowConfig, *, data_start: datetime, data_end: datetime
) -> tuple[Window, ...]:
    if config.window_type == WindowType.ROLLING:
        return _generate_rolling(config, data_start, data_end)
    if config.window_type == WindowType.EXPANDING:
        return _generate_expanding(config, data_start, data_end)
    return _generate_anchored(config, data_start, data_end)


def _generate_rolling(
    config: WindowConfig, data_start: datetime, data_end: datetime
) -> tuple[Window, ...]:
    training_duration = timedelta(days=config.training_duration_days)
    testing_duration = timedelta(days=config.testing_duration_days)
    step = timedelta(days=config.step_size_days)

    windows = []
    train_start = data_start
    index = 0
    while True:
        train_end = train_start + training_duration
        test_start = train_end
        test_end = test_start + testing_duration
        if test_end > data_end:
            break
        windows.append(
            Window(
                window_index=index,
                train_start=train_start,
                train_end=train_end,
                test_start=test_start,
                test_end=test_end,
            )
        )
        train_start += step
        index += 1
    return tuple(windows)


def _generate_expanding(
    config: WindowConfig, data_start: datetime, data_end: datetime
) -> tuple[Window, ...]:
    training_duration = timedelta(days=config.training_duration_days)
    testing_duration = timedelta(days=config.testing_duration_days)
    step = timedelta(days=config.step_size_days)

    windows = []
    train_start = data_start
    train_end = train_start + training_duration
    index = 0
    while True:
        test_start = train_end
        test_end = test_start + testing_duration
        if test_end > data_end:
            break
        windows.append(
            Window(
                window_index=index,
                train_start=train_start,
                train_end=train_end,
                test_start=test_start,
                test_end=test_end,
            )
        )
        train_end += step
        index += 1
    return tuple(windows)


def _generate_anchored(
    config: WindowConfig, data_start: datetime, data_end: datetime
) -> tuple[Window, ...]:
    training_duration = timedelta(days=config.training_duration_days)
    testing_duration = timedelta(days=config.testing_duration_days)
    step = timedelta(days=config.step_size_days)

    train_start = data_start
    train_end = train_start + training_duration

    windows = []
    test_start = train_end
    index = 0
    while True:
        test_end = test_start + testing_duration
        if test_end > data_end:
            break
        windows.append(
            Window(
                window_index=index,
                train_start=train_start,
                train_end=train_end,
                test_start=test_start,
                test_end=test_end,
            )
        )
        test_start += step
        index += 1
    return tuple(windows)
