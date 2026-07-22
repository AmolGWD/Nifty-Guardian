import pytest

from app.api.signals import signals_router, signals_service
from app.api.signals.signals_service import SignalEngineRuntimeService


@pytest.fixture
def fresh_service(monkeypatch: pytest.MonkeyPatch) -> SignalEngineRuntimeService:
    """
    A brand-new `SignalEngineRuntimeService`, swapped into both the
    service module and the router - the same `fresh_service` pattern
    `tests/api/dashboard/conftest.py` already established, so tests
    never share one process-wide session (or leave background threads
    from a previous test still running).
    """
    service = SignalEngineRuntimeService()
    monkeypatch.setattr(signals_service, "signal_engine_runtime_service", service)
    monkeypatch.setattr(signals_router, "signal_engine_runtime_service", service)
    return service
