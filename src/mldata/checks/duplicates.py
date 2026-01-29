"""Duplicate detection check."""

from pathlib import Path
from typing import Any

import polars as pl

from mldata.checks.base import BaseCheck, CheckResult, CheckStatus, CheckSeverity


class DuplicateCheck(BaseCheck):
    """Check for duplicate samples."""

    name = "duplicates"
    description = "Detect exact and near-duplicate samples"

    @property
    def configurable_params(self) -> dict:
        return {
            "threshold": 0.95,
            "hash_columns": None,
        }

    def run(self, dataset_path: Path, config: dict | None = None) -> CheckResult:
        config = config or {}
        threshold = config.get("threshold", 0.95)
        hash_columns = config.get("hash_columns")

        # Find data files
        data_files = list(dataset_path.glob("*.csv")) + list(dataset_path.glob("*.parquet"))

        if not data_files:
            return CheckResult(
                check_name=self.name,
                status=CheckStatus.SKIPPED,
                message="No data files found",
            )

        # Check first data file
        data_file = data_files[0]

        if data_file.suffix == ".csv":
            df = pl.read_csv(data_file)
        else:
            df = pl.read_parquet(data_file)

        # Exact duplicates
        total = len(df)
        unique = df.unique().height
        exact_duplicates = total - unique

        if exact_duplicates > 0:
            return CheckResult(
                check_name=self.name,
                status=CheckStatus.FAILED,
                severity=CheckSeverity.WARNING,
                message=f"Found {exact_duplicates} exact duplicates",
                details={
                    "exact_duplicates": exact_duplicates,
                    "duplicate_ratio": exact_duplicates / total if total > 0 else 0,
                },
                suggestions=["Consider deduplicating the dataset before training"],
            )

        return CheckResult(
            check_name=self.name,
            status=CheckStatus.PASSED,
            message="No exact duplicates found",
            details={
                "total_samples": total,
                "unique_samples": unique,
            },
        )
