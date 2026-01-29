"""Missing value check."""

from pathlib import Path

import polars as pl

from mldata.checks.base import BaseCheck, CheckResult, CheckSeverity, CheckStatus


class MissingValueCheck(BaseCheck):
    """Check for missing values."""

    name = "missing_values"
    description = "Detect missing/null values"

    @property
    def configurable_params(self) -> dict:
        return {
            "max_missing_ratio": 0.05,
            "columns": None,
        }

    def run(self, dataset_path: Path, config: dict | None = None) -> CheckResult:
        config = config or {}
        max_missing_ratio = config.get("max_missing_ratio", 0.05)
        columns = config.get("columns")

        # Find data files
        data_files = list(dataset_path.glob("*.csv")) + list(dataset_path.glob("*.parquet"))

        if not data_files:
            return CheckResult(
                check_name=self.name,
                status=CheckStatus.SKIPPED,
                message="No data files found",
            )

        data_file = data_files[0]

        if data_file.suffix == ".csv":
            df = pl.read_csv(data_file)
        else:
            df = pl.read_parquet(data_file)

        total = len(df)
        issues = []
        total_missing = 0

        for col_name in df.columns:
            if columns and col_name not in columns:
                continue

            missing_count = df[col_name].null_count()
            missing_ratio = missing_count / total if total > 0 else 0

            if missing_ratio > max_missing_ratio:
                issues.append(
                    {
                        "column": col_name,
                        "missing_count": missing_count,
                        "missing_ratio": missing_ratio,
                    }
                )
                total_missing += missing_count

        if issues:
            return CheckResult(
                check_name=self.name,
                status=CheckStatus.FAILED,
                severity=CheckSeverity.WARNING,
                message=f"Found {len(issues)} columns with excessive missing values",
                details={
                    "issues": issues,
                    "total_missing": total_missing,
                    "total_cells": total * len(df.columns),
                },
                suggestions=[
                    "Consider imputing missing values",
                    "Remove columns with too many missing values",
                ],
            )

        return CheckResult(
            check_name=self.name,
            status=CheckStatus.PASSED,
            message="No excessive missing values found",
            details={
                "total_missing": total_missing,
                "total_cells": total * len(df.columns),
            },
        )
