"""
POST /api/runtime/{start,pause,resume,stop,replay} and
GET /api/runtime/{health,state} - the Runtime Engine's control surface.

Every action delegates directly to `dashboard_runtime_service`; this
router adds nothing beyond translating `DashboardConflictError` (an
action that conflicts with the engine's current session state - e.g.
pausing before starting) into a 409, mirroring
`app.runtime.session_controller.InvalidSessionTransitionError`'s own
meaning at the HTTP layer.
"""

from fastapi import APIRouter, HTTPException

from app.api.dashboard.dashboard_models import RuntimeStatsResponse
from app.api.dashboard.dashboard_service import DashboardConflictError, dashboard_runtime_service
from app.api.dashboard.runtime_models import ReplayRequest, RuntimeStateResponse
from app.runtime.health import HealthSnapshot

router = APIRouter(prefix="/api/runtime", tags=["Runtime"])


@router.get("/health", response_model=HealthSnapshot)
def get_runtime_health() -> HealthSnapshot:
    return dashboard_runtime_service.health_snapshot()


@router.get("/state", response_model=RuntimeStateResponse)
def get_runtime_state() -> RuntimeStateResponse:
    return RuntimeStateResponse(state=dashboard_runtime_service.runtime_state().value)


@router.post("/start", response_model=RuntimeStatsResponse)
def start_runtime_session() -> RuntimeStatsResponse:
    try:
        return dashboard_runtime_service.start()
    except DashboardConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/pause", response_model=RuntimeStatsResponse)
def pause_runtime_session() -> RuntimeStatsResponse:
    try:
        return dashboard_runtime_service.pause()
    except DashboardConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/resume", response_model=RuntimeStatsResponse)
def resume_runtime_session() -> RuntimeStatsResponse:
    try:
        return dashboard_runtime_service.resume()
    except DashboardConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/stop", response_model=RuntimeStatsResponse)
def stop_runtime_session() -> RuntimeStatsResponse:
    try:
        return dashboard_runtime_service.stop()
    except DashboardConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/replay", response_model=RuntimeStatsResponse)
def replay_runtime_session(request: ReplayRequest) -> RuntimeStatsResponse:
    return dashboard_runtime_service.replay(
        replay_speed=request.replay_speed, maximum_candles=request.maximum_candles
    )
