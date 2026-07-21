"""
Maximum concurrent positions: caps how many positions can be open at
once, independent of capital exposure (a portfolio could have capital
room but still be too operationally complex to manage past a position
count limit).
"""


def is_within_max_concurrent_positions(open_positions: int, max_concurrent_positions: int) -> bool:
    return open_positions < max_concurrent_positions
