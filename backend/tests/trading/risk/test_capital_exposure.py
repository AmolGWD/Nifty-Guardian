from app.trading.risk.capital_exposure import is_within_capital_exposure


def test_within_exposure_with_room_to_spare() -> None:
    assert is_within_capital_exposure(0.0, 33_300.0, 100_000.0, 50.0) is True


def test_not_within_exposure_when_projected_exceeds_maximum() -> None:
    assert is_within_capital_exposure(9_000.0, 33_300.0, 100_000.0, 10.0) is False


def test_within_exposure_at_exact_boundary() -> None:
    assert is_within_capital_exposure(0.0, 50_000.0, 100_000.0, 50.0) is True


def test_not_within_exposure_one_unit_over_boundary() -> None:
    assert is_within_capital_exposure(0.0, 50_001.0, 100_000.0, 50.0) is False
