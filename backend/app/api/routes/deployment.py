"""
Deployment-only endpoints: liveness/readiness probes and a metrics
snapshot, all for an orchestrator (Docker/Kubernetes/a load balancer
health check) to poll - not for `GET /health` (Phase 1's existing
service-status endpoint, untouched). No trading logic anywhere here.

`/health/live` answers "is this process able to respond to a request
at all" - it never touches the database, so a slow/unavailable DB
never makes an orchestrator kill and restart an otherwise-healthy
process. `/health/ready` answers "is this process ready to serve real
traffic" - it does check the database, since a process that can't
reach its own database isn't actually ready.
"""

import logging
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Response, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.observability.diagnostics import get_app_metadata, get_runtime_diagnostics
from app.observability.metrics import metrics_registry
from app.observability.startup import validate_startup

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/health", tags=["Deployment"])

DbSession = Annotated[Session, Depends(get_db)]


class LivenessResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    status: Literal["alive"]


class ReadinessCheck(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str
    ok: bool
    detail: str


class ReadinessResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    status: Literal["ready", "not_ready"]
    checks: list[ReadinessCheck]


@router.get("/live", response_model=LivenessResponse)
def liveness() -> LivenessResponse:
    return LivenessResponse(status="alive")


@router.get("/ready", response_model=ReadinessResponse)
def readiness(db: DbSession, response: Response) -> ReadinessResponse:
    checks: list[ReadinessCheck] = []

    try:
        db.execute(text("SELECT 1"))
        checks.append(ReadinessCheck(name="database", ok=True, detail="reachable"))
    except Exception as exc:
        logger.exception("readiness: database check failed")
        checks.append(ReadinessCheck(name="database", ok=False, detail=str(exc)))

    startup_errors = [issue for issue in validate_startup(settings) if issue.level == "error"]
    checks.append(
        ReadinessCheck(
            name="configuration",
            ok=not startup_errors,
            detail="ok" if not startup_errors else "; ".join(i.message for i in startup_errors),
        )
    )

    overall_ok = all(check.ok for check in checks)
    if not overall_ok:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return ReadinessResponse(status="ready" if overall_ok else "not_ready", checks=checks)


@router.get("/metadata")
def metadata() -> dict[str, object]:
    app_metadata = get_app_metadata(app_name=settings.app_name, environment=settings.environment)
    runtime_diagnostics = get_runtime_diagnostics()
    return {
        "app": app_metadata.model_dump(),
        "runtime": runtime_diagnostics.model_dump(mode="json"),
    }


@router.get("/metrics")
def metrics() -> dict[str, dict[str, float]]:
    return metrics_registry.snapshot()
