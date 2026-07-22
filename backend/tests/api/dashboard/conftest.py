import pytest

from app.api.dashboard import dashboard_router, dashboard_service, runtime_router
from app.api.dashboard.dashboard_service import DashboardRuntimeService


@pytest.fixture
def fresh_service(monkeypatch: pytest.MonkeyPatch) -> DashboardRuntimeService:
    """
    A brand-new `DashboardRuntimeService`, swapped into every place that
    imported the module-level singleton by name - `dashboard_service.py`
    itself and both routers, which each bound `dashboard_runtime_service`
    into their own module namespace at import time. Without this, tests
    would share one process-wide session across the whole test run.
    """
    service = DashboardRuntimeService()
    monkeypatch.setattr(dashboard_service, "dashboard_runtime_service", service)
    monkeypatch.setattr(dashboard_router, "dashboard_runtime_service", service)
    monkeypatch.setattr(runtime_router, "dashboard_runtime_service", service)
    return service
