"""
Parameter Injection Framework (Phase 15).

Public surface: StrategyParameters (injected into EMABreakoutStrategy),
RiskParameters (app.trading.risk.models.RiskConfig re-exported under
this package's naming convention - see risk_config.py), SessionParameters
(documented, not yet wired - see session_config.py), and PARAMETER_CATALOG
(mirrored by hand in docs/PARAMETER_CATALOG.md).

RiskParameters is deliberately NOT imported eagerly above: risk_config.py
imports from app.trading.risk.models, and app.trading.risk.models imports
from app.config.defaults - if this package's __init__ eagerly imported
risk_config too, importing app.trading.risk.models first (as many tests
do directly) would re-enter this half-initialized package and fail with
a circular import. __getattr__ (PEP 562) defers that one import until
`app.config.RiskParameters` is actually accessed.
"""

from app.config.parameter_catalog import PARAMETER_CATALOG, ParameterDescriptor
from app.config.session_config import SessionParameters
from app.config.strategy_config import StrategyParameters
from app.config.validation import ParameterValidationError

__all__ = [
    "ParameterDescriptor",
    "ParameterValidationError",
    "PARAMETER_CATALOG",
    "RiskParameters",
    "SessionParameters",
    "StrategyParameters",
]


def __getattr__(name: str) -> object:
    if name == "RiskParameters":
        from app.config.risk_config import RiskParameters

        return RiskParameters
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
