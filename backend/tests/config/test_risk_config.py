"""
RiskParameters is a plain re-export of app.trading.risk.models.RiskConfig
(see app/config/risk_config.py's docstring) - these tests exist to prove
that re-export actually works and stays identical to the underlying
class, not to re-test RiskConfig's own behavior (see
tests/trading/risk/test_models.py for that).
"""

from app.config.risk_config import RiskParameters
from app.trading.risk.models import RiskConfig


def test_risk_parameters_is_the_same_class_as_risk_config() -> None:
    assert RiskParameters is RiskConfig


def test_risk_parameters_default_construction_matches_risk_config() -> None:
    assert RiskParameters() == RiskConfig()
