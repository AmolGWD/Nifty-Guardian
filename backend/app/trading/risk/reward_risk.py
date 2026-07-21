"""
Reward/risk calculation: the ratio actually achieved between the
target distance and the stop-loss distance, computed independently
rather than assumed equal to `RiskConfig.target_atr_multiplier /
stop_loss_atr_multiplier`, so it stays correct even if stop-loss/target
are ever derived a different way in the future.
"""


def calculate_reward_risk_ratio(stop_loss_distance: float, target_distance: float) -> float:
    if stop_loss_distance <= 0:
        return 0.0

    return round(target_distance / stop_loss_distance, 4)
