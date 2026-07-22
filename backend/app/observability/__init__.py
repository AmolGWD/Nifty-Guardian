"""
Observability: structured logging, a basic metrics registry, startup
validation, and app/runtime diagnostics for production deployment.
Purely additive - no trading, broker, or runtime logic lives here.
"""

from app.observability.diagnostics import (
    AppMetadata,
    RuntimeDiagnostics,
    get_app_metadata,
    get_runtime_diagnostics,
)
from app.observability.logging import (
    JsonFormatter,
    configure_structured_logging,
    get_request_id,
    set_request_id,
)
from app.observability.metrics import MetricsRegistry, metrics_registry, record_request
from app.observability.startup import StartupIssue, run_startup_diagnostics, validate_startup

__all__ = [
    "AppMetadata",
    "JsonFormatter",
    "MetricsRegistry",
    "RuntimeDiagnostics",
    "StartupIssue",
    "configure_structured_logging",
    "get_app_metadata",
    "get_request_id",
    "get_runtime_diagnostics",
    "metrics_registry",
    "record_request",
    "run_startup_diagnostics",
    "set_request_id",
    "validate_startup",
]
