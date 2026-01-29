"""Quality report models."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


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
    details: dict[str, Any] = Field(default_factory=dict)
    suggestions: list[str] = Field(default_factory=list)
    duration_ms: float | None = None


class QualityReport(BaseModel):
    """Quality report for a dataset."""

    version: str = "1.0"
    generated_at: datetime
    dataset_path: str
    dataset_uri: str | None = None
    num_samples: int | None = None
    num_columns: int | None = None
    summary: dict[str, Any] = Field(default_factory=dict)
    checks: list[CheckResult] = Field(default_factory=list)

    @classmethod
    def create(cls, dataset_path: str, dataset_uri: str | None = None) -> "QualityReport":
        """Create a new quality report."""
        from datetime import timezone

        return cls(
            generated_at=datetime.now(timezone.utc),
            dataset_path=dataset_path,
            dataset_uri=dataset_uri,
        )

    def to_json(self, path: str) -> None:
        """Write report to JSON file."""
        import json

        with open(path, "w") as f:
            json.dump(self.model_dump(mode="json"), f, indent=2)

    def to_markdown(self, path: str) -> None:
        """Write report to Markdown file."""
        lines = [
            "# Quality Report",
            f"Generated: {self.generated_at.isoformat()}",
            f"Dataset: {self.dataset_path}",
            "",
            "## Summary",
            f"- Total Checks: {self.summary.get('total_checks', 0)}",
            f"- Passed: {self.summary.get('passed', 0)}",
            f"- Failed: {self.summary.get('failed', 0)}",
            f"- Warnings: {self.summary.get('warnings', 0)}",
            f"- Errors: {self.summary.get('errors', 0)}",
            "",
            "## Check Results",
        ]

        for check in self.checks:
            status_icon = "✓" if check.status.value == "passed" else "✗" if check.status.value == "failed" else "⚠"
            lines.append(f"### {status_icon} {check.check_name}")
            lines.append(f"- Status: {check.status.value}")
            lines.append(f"- Severity: {check.severity.value}")
            lines.append(f"- Message: {check.message}")
            if check.details:
                lines.append("- Details:")
                for k, v in check.details.items():
                    lines.append(f"  - {k}: {v}")
            if check.suggestions:
                lines.append("- Suggestions:")
                for s in check.suggestions:
                    lines.append(f"  - {s}")
            lines.append("")

        with open(path, "w") as f:
            f.write("\n".join(lines))
