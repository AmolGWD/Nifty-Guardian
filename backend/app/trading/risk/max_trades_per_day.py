"""
Maximum trades per day: caps how many trades can be taken in a single
session, independent of how any of them performed.
"""


def is_within_max_trades_per_day(trades_taken_today: int, max_trades_per_day: int) -> bool:
    return trades_taken_today < max_trades_per_day
