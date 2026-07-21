"""
Daily loss limit: blocks further risk-taking once today's realized
loss has reached the configured maximum.
"""


def is_within_daily_loss_limit(realized_loss_today: float, max_daily_loss: float) -> bool:
    return realized_loss_today < max_daily_loss
