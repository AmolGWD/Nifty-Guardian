"""
Put Call Ratio.

Takes plain OI totals rather than any market_data schema - Phase 4's
OptionContract does not carry open interest (it's built on Kite's ltp()
response, which doesn't include OI; only the richer quote() call does).
Wiring up a real OI source is later work; this calculator only needs
the two numbers, from wherever they end up coming from.
"""


def calculate_put_call_ratio(total_put_oi: int, total_call_oi: int) -> float:
    if total_call_oi == 0:
        raise ValueError("Cannot calculate Put Call Ratio with zero call open interest")

    return round(total_put_oi / total_call_oi, 4)
