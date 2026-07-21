"""
Existing position guard (interface/stub only). Paper trading (a later
phase) doesn't exist yet, so there is no real source for "is there
already an open position" - callers supply it explicitly.
"""


def is_position_guard_ok(has_open_position: bool) -> bool:
    return not has_open_position
