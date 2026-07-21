"""
The single, immutable output of one strategy's evaluation.

No confidence score - `strength` is a deliberately coarse, categorical
read (Strong/Moderate/Weak), not a numeric percentage. Confidence
scoring is explicitly out of scope for this phase.
"""

from enum import StrEnum

from pydantic import BaseModel, ConfigDict


class StrategyDirection(StrEnum):
    LONG = "Long"
    SHORT = "Short"
    NONE = "None"


class StrategyStrength(StrEnum):
    STRONG = "Strong"
    MODERATE = "Moderate"
    WEAK = "Weak"


class StrategyEvaluation(BaseModel):
    model_config = ConfigDict(frozen=True)

    strategy_name: str

    valid: bool
    direction: StrategyDirection
    strength: StrategyStrength

    reasons: list[str]
    warnings: list[str]
