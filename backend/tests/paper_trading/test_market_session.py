from datetime import date, datetime, time

import pytest
from pydantic import ValidationError

from app.paper_trading.market_session import ConfigurableCalendar, SessionPhase, SessionWindows

_STANDARD_WINDOWS = SessionWindows(
    pre_open_start=time(9, 0),
    open_start=time(9, 15),
    open_end=time(15, 30),
    lunch_start=time(12, 0),
    lunch_end=time(13, 0),
    after_hours_end=time(16, 0),
)


def test_pre_open_phase() -> None:
    calendar = ConfigurableCalendar(_STANDARD_WINDOWS)
    assert calendar.session_phase(datetime(2026, 1, 5, 9, 10)) == SessionPhase.PRE_OPEN


def test_open_phase() -> None:
    calendar = ConfigurableCalendar(_STANDARD_WINDOWS)
    assert calendar.session_phase(datetime(2026, 1, 5, 11, 0)) == SessionPhase.OPEN


def test_lunch_phase() -> None:
    calendar = ConfigurableCalendar(_STANDARD_WINDOWS)
    assert calendar.session_phase(datetime(2026, 1, 5, 12, 30)) == SessionPhase.LUNCH


def test_after_hours_phase() -> None:
    calendar = ConfigurableCalendar(_STANDARD_WINDOWS)
    assert calendar.session_phase(datetime(2026, 1, 5, 15, 45)) == SessionPhase.AFTER_HOURS


def test_close_phase_after_after_hours_ends() -> None:
    calendar = ConfigurableCalendar(_STANDARD_WINDOWS)
    assert calendar.session_phase(datetime(2026, 1, 5, 18, 0)) == SessionPhase.CLOSE


def test_weekend_is_a_holiday() -> None:
    calendar = ConfigurableCalendar(_STANDARD_WINDOWS)
    assert calendar.session_phase(datetime(2026, 1, 10, 11, 0)) == SessionPhase.HOLIDAY  # Saturday


def test_explicit_holiday_date_is_a_holiday() -> None:
    calendar = ConfigurableCalendar(_STANDARD_WINDOWS, holidays={date(2026, 1, 26)})
    assert calendar.session_phase(datetime(2026, 1, 26, 11, 0)) == SessionPhase.HOLIDAY


def test_is_trading_day() -> None:
    calendar = ConfigurableCalendar(_STANDARD_WINDOWS, holidays={date(2026, 1, 26)})
    assert calendar.is_trading_day(date(2026, 1, 5)) is True
    assert calendar.is_trading_day(date(2026, 1, 10)) is False  # weekend
    assert calendar.is_trading_day(date(2026, 1, 26)) is False  # explicit holiday


def test_no_lunch_window_configured() -> None:
    windows = SessionWindows(
        pre_open_start=time(9, 0), open_start=time(9, 15), open_end=time(15, 30)
    )
    calendar = ConfigurableCalendar(windows)
    assert calendar.session_phase(datetime(2026, 1, 5, 12, 30)) == SessionPhase.OPEN


def test_rejects_pre_open_after_open_start() -> None:
    with pytest.raises(ValidationError, match="pre_open_start"):
        SessionWindows(pre_open_start=time(9, 20), open_start=time(9, 15), open_end=time(15, 30))


def test_rejects_lunch_start_without_lunch_end() -> None:
    with pytest.raises(ValidationError, match="lunch_start and lunch_end"):
        SessionWindows(
            pre_open_start=time(9, 0), open_start=time(9, 15), open_end=time(15, 30),
            lunch_start=time(12, 0),
        )


def test_rejects_lunch_window_outside_open_window() -> None:
    with pytest.raises(ValidationError, match="lunch window"):
        SessionWindows(
            pre_open_start=time(9, 0), open_start=time(9, 15), open_end=time(15, 30),
            lunch_start=time(8, 0), lunch_end=time(8, 30),
        )


def test_rejects_after_hours_end_before_open_end() -> None:
    with pytest.raises(ValidationError, match="after_hours_end"):
        SessionWindows(
            pre_open_start=time(9, 0), open_start=time(9, 15), open_end=time(15, 30),
            after_hours_end=time(15, 0),
        )


def test_no_nse_specific_default_values_hardcoded_in_module() -> None:
    """Structural guard: SessionWindows fields have no defaults - every value must be supplied."""
    assert all(
        SessionWindows.model_fields[name].is_required()
        for name in ("pre_open_start", "open_start", "open_end")
    )
