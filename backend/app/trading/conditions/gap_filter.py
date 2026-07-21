"""
Gap filter (framework only). No live "previous close vs today's open"
data source is wired up anywhere yet - Phase 4's schemas don't carry a
previous-close reference for options - so this only evaluates when a
gap percentage is actually supplied. With none supplied, it does not
block trading, since there's nothing yet to evaluate.
"""


def is_gap_filter_ok(gap_percent: float | None, max_gap_percent: float) -> bool:
    if gap_percent is None:
        return True

    return abs(gap_percent) <= max_gap_percent
