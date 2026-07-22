"""GET /api/dashboard - the complete dashboard snapshot."""

from fastapi import APIRouter

from app.api.dashboard.dashboard_models import DashboardSnapshotResponse
from app.api.dashboard.dashboard_service import dashboard_runtime_service

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("", response_model=DashboardSnapshotResponse)
def get_dashboard() -> DashboardSnapshotResponse:
    return dashboard_runtime_service.dashboard_snapshot()
