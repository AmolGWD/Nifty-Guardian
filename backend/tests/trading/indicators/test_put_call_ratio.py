import pytest

from app.trading.indicators.put_call_ratio import calculate_put_call_ratio


def test_pcr_matches_hand_calculated_value() -> None:
    assert calculate_put_call_ratio(total_put_oi=180_000, total_call_oi=120_000) == 1.5


def test_pcr_equal_oi_is_one() -> None:
    assert calculate_put_call_ratio(total_put_oi=100, total_call_oi=100) == 1.0


def test_pcr_raises_on_zero_call_oi() -> None:
    with pytest.raises(ValueError, match="zero call open interest"):
        calculate_put_call_ratio(total_put_oi=100, total_call_oi=0)
