"""
Centralized logging configuration.

All modules should obtain a logger via `logging.getLogger(__name__)`
and use it instead of `print()`. This module wires up the root
handler and format once, at application startup.
"""

import logging
import sys

from app.core.config import settings


def configure_logging() -> None:
    logging.basicConfig(
        level=settings.log_level.upper(),
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        stream=sys.stdout,
        force=True,
    )
