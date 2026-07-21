"""
Minimum liquidity framework: requires a contract's volume to meet a
configured minimum. No real per-contract volume data source exists yet
- Phase 4's OptionContract doesn't carry volume/OI, the same gap
already flagged for Open Interest in Phase 5 - so this passes
automatically when no volume figure is supplied.
"""


def is_liquidity_ok(volume: int | None, min_volume: int) -> bool:
    if volume is None:
        return True

    return volume >= min_volume
