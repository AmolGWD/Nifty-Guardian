"""
Shared validation error type and range-checking helpers for app.config's
parameter models. Kept here (rather than duplicated per model) so every
config validator raises the same exception type with the same message
shape.
"""


class ParameterValidationError(ValueError):
    pass


def validate_range(
    name: str, value: float, minimum: float, maximum: float
) -> None:
    if not (minimum <= value <= maximum):
        raise ParameterValidationError(
            f"{name}={value} is out of the allowed range [{minimum}, {maximum}]"
        )


def validate_less_than(low_name: str, low_value: float, high_name: str, high_value: float) -> None:
    if low_value >= high_value:
        raise ParameterValidationError(
            f"{low_name}={low_value} must be less than {high_name}={high_value}"
        )
