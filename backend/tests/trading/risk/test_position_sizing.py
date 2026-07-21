from app.trading.risk.position_sizing import calculate_position_size


def test_position_size_matches_hand_calculated_value() -> None:
    assert calculate_position_size(100_000.0, 1.0, 3.0) == 333


def test_position_size_floors_to_zero_when_capital_too_small() -> None:
    assert calculate_position_size(100.0, 1.0, 3.0) == 0


def test_position_size_is_zero_when_stop_loss_distance_is_zero() -> None:
    assert calculate_position_size(100_000.0, 1.0, 0.0) == 0


def test_position_size_is_zero_when_stop_loss_distance_is_negative() -> None:
    assert calculate_position_size(100_000.0, 1.0, -5.0) == 0
