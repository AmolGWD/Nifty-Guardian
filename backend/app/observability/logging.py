"""
Structured (JSON) logging for production deployments, alongside the
existing plain-text `app.core.logging.configure_logging()` used for
local development. Neither replaces the other - `LOG_FORMAT` picks
which one `app.main` wires up at startup. Every module still just
calls `logging.getLogger(__name__)`; this module only changes how a
record is *rendered*, never what gets logged or by whom.

A request ID (set per-request by `app.main`'s middleware) is attached
to every log record emitted while handling that request, via a
`ContextVar` - the same mechanism `contextvars` documents for exactly
this "ambient, per-async-task value" use case.
"""

import json
import logging
import sys
from contextvars import ContextVar
from datetime import UTC, datetime
from typing import Literal

_request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)

_STANDARD_LOG_RECORD_FIELDS = frozenset(
    logging.LogRecord("", 0, "", 0, "", (), None).__dict__.keys()
)


def set_request_id(request_id: str | None) -> None:
    _request_id_var.set(request_id)


def get_request_id() -> str | None:
    return _request_id_var.get()


class JsonFormatter(logging.Formatter):
    """Renders each `LogRecord` as one JSON object per line."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, object] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        request_id = get_request_id()
        if request_id is not None:
            payload["request_id"] = request_id
        if record.exc_info is not None:
            payload["exception"] = self.formatException(record.exc_info)

        for key, value in record.__dict__.items():
            if key not in _STANDARD_LOG_RECORD_FIELDS and key not in payload:
                payload[key] = value

        return json.dumps(payload, default=str)


def configure_structured_logging(*, level: str, log_format: Literal["json", "text"]) -> None:
    """
    Replaces every handler on the root logger with a single stdout
    handler, formatted per `log_format`. `force=True` mirrors
    `app.core.logging.configure_logging()`'s own approach, so calling
    either one at startup always wins regardless of import order.
    """
    handler = logging.StreamHandler(stream=sys.stdout)
    if log_format == "json":
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(
            logging.Formatter(
                fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )

    root = logging.getLogger()
    root.setLevel(level.upper())
    root.handlers = [handler]
