"""
Position sizing: how many units can be taken such that a stop-loss hit
loses no more than the configured risk-per-trade percentage of capital.
"""

import math


def calculate_position_size(
    capital: float, risk_per_trade_percent: float, stop_loss_distance: float
) -> int:
    if stop_loss_distance <= 0:
        return 0

    risk_amount = capital * (risk_per_trade_percent / 100)

    return math.floor(risk_amount / stop_loss_distance)
