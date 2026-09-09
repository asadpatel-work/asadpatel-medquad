"""Structured JSON logging and telemetry setup."""

import json
import logging
import sys
from datetime import UTC, datetime
from typing import Any


class JSONFormatter(logging.Formatter):
    """Custom formatter producing GCP Cloud Logging compatible JSON logs."""

    def format(self, record: logging.LogRecord) -> str:
        log_payload: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "severity": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
            "module": record.module,
            "line": record.lineno,
        }
        if hasattr(record, "request_id"):
            log_payload["requestId"] = record.request_id
        if hasattr(record, "trace_id"):
            log_payload["logging.googleapis.com/trace"] = record.trace_id
        if hasattr(record, "span_id"):
            log_payload["logging.googleapis.com/spanId"] = record.span_id
        if record.exc_info:
            log_payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_payload)


def setup_logging(log_level: str = "INFO") -> None:
    """Configures root logger with JSON output."""
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level.upper())

    for handler in list(root_logger.handlers):
        root_logger.removeHandler(handler)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())
    root_logger.addHandler(handler)
