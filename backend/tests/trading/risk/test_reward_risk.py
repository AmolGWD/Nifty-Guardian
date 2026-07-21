from app.trading.risk.reward_risk import calculate_reward_risk_ratio


def test_reward_risk_ratio_matches_hand_calculated_value() -> None:
    assert calculate_reward_risk_ratio(3.0, 6.0) == 2.0


def test_reward_risk_ratio_below_one() -> None:
    assert calculate_reward_risk_ratio(4.0, 2.0) == 0.5


def test_reward_risk_ratio_is_zero_when_stop_loss_distance_is_zero() -> None:
    assert calculate_reward_risk_ratio(0.0, 6.0) == 0.0
