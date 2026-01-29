"""Logging utilities."""

import logging
from typing import Any

from rich.logging import RichHandler


def setup_logging(
    level: str = "INFO",
    format: str | None = None,
    verbose: bool = False,
) -> logging.Logger:
    """Set up structured logging.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format: Custom log format
        verbose: Enable verbose (debug) logging

    Returns:
        Configured logger instance
    """
    if verbose:
        level = "DEBUG"

    # Remove any existing handlers
    root_logger = logging.getLogger()
    root_logger.handlers = []

    # Configure Rich handler
    handler = RichHandler(
        show_time=True,
        show_level=True,
        show_path=verbose,
        rich_tracebacks=True,
    )

    formatter = logging.Formatter(
        format or "%(message)s",
        datefmt="[%X]",
    )
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)
    root_logger.setLevel(level)

    # Reduce noise from third-party libraries
    logging.getLogger("httpx").setLevel("WARNING")
    logging.getLogger("httpcore").setLevel("WARNING")
    logging.getLogger("datasets").setLevel("WARNING")

    return logging.getLogger("mldata")


class MldataLogger:
    """Structured logger for mldata operations."""

    def __init__(self, name: str = "mldata"):
        self.logger = logging.getLogger(name)

    def log_operation(self, operation: str, **kwargs: Any) -> None:
        """Log an operation with structured data."""
        msg = f"Starting {operation}"
        if kwargs:
            self.logger.debug(msg, extra={"structured": True, "operation": operation, **kwargs})
        else:
            self.logger.debug(msg)

    def log_result(self, operation: str, success: bool, **kwargs: Any) -> None:
        """Log operation result."""
        status = "completed" if success else "failed"
        self.logger.info(f"{operation} {status}", extra={"structured": True, "operation": operation, "status": status, **kwargs})
