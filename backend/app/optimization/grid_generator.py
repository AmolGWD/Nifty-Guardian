"""
Deterministic Cartesian product of a ParameterSpace's dimensions - no
randomization anywhere, per the CTO brief. Combination order is fixed:
`itertools.product` over each parameter's own `values()` (already
generated in a fixed minimum-to-maximum order), varying the last
parameter fastest - so the same `ParameterSpace` always yields the same
combinations in the same order, run to run.
"""

from itertools import product

from app.optimization.models import GridValue
from app.optimization.parameter_space import ParameterSpace


def generate_grid(space: ParameterSpace) -> tuple[dict[str, GridValue], ...]:
    names = space.dimension_names()
    value_lists = [parameter.values() for parameter in space.parameters]

    return tuple(
        dict(zip(names, combination, strict=True)) for combination in product(*value_lists)
    )
