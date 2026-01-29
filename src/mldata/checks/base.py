"""Base check interface."""

from abc import ABC, abstractmethod
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel


class CheckSeverity(str, Enum):
    """Severity level of a quality check."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class CheckStatus(str, Enum):
    """Status of a quality check."""

    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


class CheckResult(BaseModel):
    """Result of a single quality check."""

    check_name: str
    status: CheckStatus
    severity: CheckSeverity = CheckSeverity.INFO
    message: str = ""
    details: dict[str, Any] = {}
    suggestions: list[str] = []
    duration_ms: float | None = None


class BaseCheck(ABC):
    """Abstract base class for quality checks."""

    name: str = "base"
    description: str = ""
    default_enabled: bool = True

    @abstractmethod
    def run(self, dataset_path: Path, config: dict | None = None) -> CheckResult:
        """Execute the check and return results.

        Args:
            dataset_path: Path to dataset directory
            config: Check configuration

        Returns:
            CheckResult
        """
        ...

    @property
    def configurable_params(self) -> dict:
        """Return configurable parameters with defaults."""
        return {}
