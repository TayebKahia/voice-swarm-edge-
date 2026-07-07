"""Structured logging utility for schema and swarm components (PRD Sec. 5.2).

Provides JSON-formatted log records ensuring all structured `extra` fields
(clamping events, ID drops, fallbacks, FSM transitions) are preserved
and verifiable in audit trails.
"""

from __future__ import annotations

import json
import logging
import sys
from typing import Any

__all__ = ["StructuredJsonFormatter", "configure_schema_logging", "get_structured_logger"]


class StructuredJsonFormatter(logging.Formatter):
    """Formats LogRecords as single-line JSON objects including all extra fields."""

    STANDARD_ATTRS = {
        "args",
        "asctime",
        "created",
        "exc_info",
        "exc_text",
        "filename",
        "funcName",
        "levelname",
        "levelno",
        "lineno",
        "module",
        "msecs",
        "message",
        "msg",
        "name",
        "pathname",
        "process",
        "processName",
        "relativeCreated",
        "stack_info",
        "thread",
        "threadName",
    }

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Include all custom structured fields passed via extra={...}
        for key, val in record.__dict__.items():
            if key not in self.STANDARD_ATTRS and not key.startswith("_"):
                payload[key] = val

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, default=str)


def configure_schema_logging(level: int = logging.INFO) -> logging.Handler:
    """Attach a structured JSON handler to the schema logger hierarchy."""
    logger = logging.getLogger("schema")
    logger.setLevel(level)

    # Avoid duplicate handlers if reconfigured
    for handler in list(logger.handlers):
        if isinstance(handler.formatter, StructuredJsonFormatter):
            return handler

    handler = logging.StreamHandler(sys.stderr)
    handler.setLevel(level)
    handler.setFormatter(StructuredJsonFormatter())
    logger.addHandler(handler)
    return handler


def get_structured_logger(name: str) -> logging.Logger:
    """Return a logger with structured logging configured."""
    configure_schema_logging()
    return logging.getLogger(name)
