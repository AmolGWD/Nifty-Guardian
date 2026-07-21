from datetime import datetime

from app.trading.analytics.equity_analysis import (
    calculate_total_return_percent,
    calculate_years_elapsed,
    daily_returns,
    largest_equity_peak,
    largest_equity_valley,
    last_equity_per_day,
)
from tests.trading.analytics.helpers import make_equity_point


def test_total_return_percent_matches_hand_calculated_value() -> None:
    assert calculate_total_return_percent(100_000.0, 105_000.0) == 5.0


def test_total_return_percent_is_zero_when_initial_capital_is_zero() -> None:
    assert calculate_total_return_percent(0.0, 105_000.0) == 0.0


def test_years_elapsed_matches_hand_calculated_value() -> None:
    curve = [
        make_equity_point(timestamp=datetime(2025, 7, 21, 10, 0)),
        make_equity_point(timestamp=datetime(2026, 7, 21, 10, 0)),
    ]

    years = calculate_years_elapsed(curve)

    assert years is not None
    assert 0.99 < years < 1.01


def test_years_elapsed_is_none_with_fewer_than_two_points() -> None:
    assert calculate_years_elapsed([make_equity_point()]) is None
    assert calculate_years_elapsed([]) is None


def test_years_elapsed_is_none_when_span_is_zero_days() -> None:
    curve = [
        make_equity_point(timestamp=datetime(2026, 7, 21, 10, 0)),
        make_equity_point(timestamp=datetime(2026, 7, 21, 11, 0)),
    ]
    assert calculate_years_elapsed(curve) is None


def test_last_equity_per_day_keeps_latest_value_each_day() -> None:
    curve = [
        make_equity_point(timestamp=datetime(2026, 7, 21, 10, 0), equity=100_000.0),
        make_equity_point(timestamp=datetime(2026, 7, 21, 15, 0), equity=101_000.0),
        make_equity_point(timestamp=datetime(2026, 7, 22, 10, 0), equity=102_000.0),
    ]

    assert last_equity_per_day(curve) == [101_000.0, 102_000.0]


def test_daily_returns_matches_hand_calculated_value() -> None:
    curve = [
        make_equity_point(timestamp=datetime(2026, 7, 21, 15, 0), equity=100_000.0),
        make_equity_point(timestamp=datetime(2026, 7, 22, 15, 0), equity=101_000.0),
        make_equity_point(timestamp=datetime(2026, 7, 23, 15, 0), equity=99_990.0),
    ]

    returns = daily_returns(curve)

    assert returns[0] == 0.01
    assert round(returns[1], 6) == round((99_990.0 - 101_000.0) / 101_000.0, 6)


def test_largest_equity_peak_and_valley() -> None:
    curve = [
        make_equity_point(equity=100_000.0),
        make_equity_point(equity=105_000.0),
        make_equity_point(equity=98_000.0),
    ]

    assert largest_equity_peak(curve) == 105_000.0
    assert largest_equity_valley(curve) == 98_000.0


def test_largest_equity_peak_and_valley_default_to_zero_when_empty() -> None:
    assert largest_equity_peak([]) == 0.0
    assert largest_equity_valley([]) == 0.0
