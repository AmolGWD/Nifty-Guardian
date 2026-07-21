from datetime import datetime

from app.trading.analytics.performance_metrics import (
    calculate_annual_return,
    calculate_cagr,
    calculate_calmar_ratio,
    calculate_recovery_factor,
    calculate_sortino_ratio,
)
from tests.trading.analytics.helpers import make_equity_point


def test_cagr_matches_hand_calculated_value() -> None:
    # 100,000 -> 121,000 over 2 years = 10% CAGR exactly (1.1^2 = 1.21)
    cagr = calculate_cagr(100_000.0, 121_000.0, 2.0)

    assert cagr is not None
    assert round(cagr, 2) == 10.0


def test_cagr_is_none_without_a_valid_time_span() -> None:
    assert calculate_cagr(100_000.0, 121_000.0, None) is None
    assert calculate_cagr(100_000.0, 121_000.0, 0.0) is None
    assert calculate_cagr(0.0, 121_000.0, 2.0) is None


def test_annual_return_matches_hand_calculated_value() -> None:
    # 10,000 profit on 100,000 capital over 2 years = 5% per year (linear)
    annual_return = calculate_annual_return(10_000.0, 100_000.0, 2.0)

    assert annual_return is not None
    assert round(annual_return, 2) == 5.0


def test_annual_return_is_none_without_a_valid_time_span() -> None:
    assert calculate_annual_return(10_000.0, 100_000.0, None) is None
    assert calculate_annual_return(10_000.0, 0.0, 2.0) is None


def test_sortino_ratio_is_none_with_insufficient_downside_data() -> None:
    curve = [
        make_equity_point(timestamp=datetime(2026, 7, 21, 10, 0), equity=100_000.0),
        make_equity_point(timestamp=datetime(2026, 7, 22, 10, 0), equity=101_000.0),
        make_equity_point(timestamp=datetime(2026, 7, 23, 10, 0), equity=102_000.0),
    ]

    assert calculate_sortino_ratio(curve) is None


def test_sortino_ratio_is_a_float_with_enough_downside_variance() -> None:
    curve = [
        make_equity_point(timestamp=datetime(2026, 7, 21, 10, 0), equity=100_000.0),
        make_equity_point(timestamp=datetime(2026, 7, 22, 10, 0), equity=101_000.0),
        make_equity_point(timestamp=datetime(2026, 7, 23, 10, 0), equity=99_000.0),
        make_equity_point(timestamp=datetime(2026, 7, 24, 10, 0), equity=98_000.0),
        make_equity_point(timestamp=datetime(2026, 7, 25, 10, 0), equity=103_000.0),
    ]

    sortino = calculate_sortino_ratio(curve)

    assert sortino is not None
    assert isinstance(sortino, float)


def test_calmar_ratio_matches_hand_calculated_value() -> None:
    assert calculate_calmar_ratio(20.0, 10.0) == 2.0


def test_calmar_ratio_is_none_without_cagr_or_drawdown() -> None:
    assert calculate_calmar_ratio(None, 10.0) is None
    assert calculate_calmar_ratio(20.0, 0.0) is None


def test_recovery_factor_matches_hand_calculated_value() -> None:
    assert calculate_recovery_factor(5_000.0, 2_500.0) == 2.0


def test_recovery_factor_is_none_without_drawdown() -> None:
    assert calculate_recovery_factor(5_000.0, 0.0) is None
