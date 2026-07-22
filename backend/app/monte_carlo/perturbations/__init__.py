"""
Independent trade-outcome perturbations - each module exposes a pure
`apply(...)` function and knows nothing about any other perturbation
module. `simulation.py` is the only place that chains them together,
in one fixed, documented order.
"""
