"""
GET/POST endpoints for the Signal Engine - entirely new, alongside
`app.api.dashboard`'s own router (never modified). No trading logic,
no broker connectivity of its own - every response reflects state
`SignalEngineRuntimeService` already computed.
"""

from fastapi import APIRouter, HTTPException, status

from app.api.signals.signals_models import (
    DailyReportResponse,
    DummyTradeResponse,
    EngineStatusResponse,
    ExportReportResponse,
    PerformanceResponse,
    SignalStateResponse,
)
from app.api.signals.signals_service import (
    SignalEngineConflictError,
    signal_engine_runtime_service,
)

router = APIRouter(prefix="/api/signals", tags=["Signals"])


@router.post("/start", response_model=EngineStatusResponse)
def start_signal_engine_session() -> EngineStatusResponse:
    try:
        return signal_engine_runtime_service.start()
    except SignalEngineConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.post("/stop", response_model=EngineStatusResponse)
def stop_signal_engine_session() -> EngineStatusResponse:
    try:
        return signal_engine_runtime_service.stop()
    except SignalEngineConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.get("/status", response_model=EngineStatusResponse)
def get_status() -> EngineStatusResponse:
    return signal_engine_runtime_service.status()


@router.get("/state", response_model=SignalStateResponse)
def get_state() -> SignalStateResponse:
    return signal_engine_runtime_service.state()


@router.get("/performance", response_model=PerformanceResponse)
def get_performance() -> PerformanceResponse:
    return signal_engine_runtime_service.performance()


@router.get("/trades", response_model=list[DummyTradeResponse])
def get_trades() -> list[DummyTradeResponse]:
    return signal_engine_runtime_service.trades()


@router.get("/report/today", response_model=DailyReportResponse)
def get_todays_report() -> DailyReportResponse:
    return signal_engine_runtime_service.report_today()


@router.post("/report/export", response_model=ExportReportResponse)
def export_report_now() -> ExportReportResponse:
    try:
        return signal_engine_runtime_service.export_report_now()
    except SignalEngineConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
