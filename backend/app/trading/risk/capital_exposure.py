"""
Capital exposure: caps total capital committed (already-deployed plus
this new trade's requirement) as a percentage of total capital.
"""


def is_within_capital_exposure(
    capital_deployed: float,
    capital_required: float,
    total_capital: float,
    max_capital_exposure_percent: float,
) -> bool:
    projected_exposure = capital_deployed + capital_required
    max_exposure = total_capital * (max_capital_exposure_percent / 100)

    return projected_exposure <= max_exposure
