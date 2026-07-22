"""
Application metadata and runtime diagnostics - what version is this,
what environment is it running in, how long has it been up. Every
value here is either a compile-time constant, an environment variable,
or a directly-observed OS fact (pid, hostname, uptime) - nothing is
computed from trading state, and nothing here ever touches
`app.trading`/`app.paper_trading`/`app.runtime`/`app.live`.
"""

import os
import platform
import socket
import time
from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict

_PROCESS_START_MONOTONIC = time.monotonic()
_PROCESS_START_WALL_CLOCK = datetime.now(UTC)

APP_VERSION = os.getenv("APP_VERSION", "2.0.0")


class AppMetadata(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str
    version: str
    environment: str
    git_commit: str
    python_version: str


class RuntimeDiagnostics(BaseModel):
    model_config = ConfigDict(frozen=True)

    started_at: datetime
    uptime_seconds: float
    process_id: int
    hostname: str


def get_app_metadata(*, app_name: str, environment: str) -> AppMetadata:
    return AppMetadata(
        name=app_name,
        version=APP_VERSION,
        environment=environment,
        git_commit=os.getenv("GIT_COMMIT", "unknown"),
        python_version=platform.python_version(),
    )


def get_runtime_diagnostics() -> RuntimeDiagnostics:
    return RuntimeDiagnostics(
        started_at=_PROCESS_START_WALL_CLOCK,
        uptime_seconds=time.monotonic() - _PROCESS_START_MONOTONIC,
        process_id=os.getpid(),
        hostname=socket.gethostname(),
    )
