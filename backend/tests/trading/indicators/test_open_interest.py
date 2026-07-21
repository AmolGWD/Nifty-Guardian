import pytest

from app.trading.indicators.open_interest import OpenInterestSignal, analyze_open_interest


@pytest.mark.parametrize(
    ("price_change", "oi_change", "expected"),
    [
        (5, 5, OpenInterestSignal.LONG_BUILDUP),
        (5, -5, OpenInterestSignal.SHORT_COVERING),
        (-5, 5, OpenInterestSignal.SHORT_BUILDUP),
        (-5, -5, OpenInterestSignal.LONG_UNWINDING),
        (0, 5, OpenInterestSignal.NEUTRAL),
        (5, 0, OpenInterestSignal.NEUTRAL),
        (0, 0, OpenInterestSignal.NEUTRAL),
    ],
)
def test_open_interest_quadrants(
    price_change: float, oi_change: float, expected: OpenInterestSignal
) -> None:
    assert analyze_open_interest(price_change, oi_change) == expected
