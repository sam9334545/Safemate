"""Logging configuration ensuring privacy and structured diagnostic logs."""

import logging
import sys
from app.core.config import settings


class PrivacyFilter(logging.Filter):
    """Filter to ensure sensitive data or large binary snippets are not logged."""

    def filter(self, record: logging.LogRecord) -> bool:
        # Guarantee no binary image chunks or base64 data leak into logs
        msg = str(record.msg)
        if "data:image" in msg or "base64" in msg.lower():
            record.msg = "[REDACTED BINARY/IMAGE DATA]"
        return True


def setup_logging() -> None:
    """Configure application-wide logging."""
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    log_format = (
        "%(asctime)s [%(levelname)s] [%(name)s] [ReqID: %(request_id)s] %(message)s"
        if "%(request_id)s" in settings.LOG_LEVEL
        else "%(asctime)s [%(levelname)s] [%(name)s] %(message)s"
    )

    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    handler.addFilter(PrivacyFilter())

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Avoid duplicate handlers if setup_logging is called multiple times
    if not any(isinstance(h, logging.StreamHandler) for h in root_logger.handlers):
        root_logger.addHandler(handler)
    else:
        # Update existing handlers
        for h in root_logger.handlers:
            h.setLevel(log_level)
            h.setFormatter(formatter)
            h.addFilter(PrivacyFilter())

    # Set third party loggers to warning to avoid clutter
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
    logging.getLogger("transformers").setLevel(logging.WARNING)
    logging.getLogger("PIL").setLevel(logging.WARNING)
