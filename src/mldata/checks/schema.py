"""Schema consistency check."""

from pathlib import Path
from typing import Any

import polars as pl

from mldata.checks.base import BaseCheck, CheckResult, CheckStatus, CheckSeverity


class SchemaConsistencyCheck(BaseCheck):
    """Check for schema consistency across splits."""

    name = "schema_consistency"
    description = "Validate schema consistency across splits"

    def run(self, dataset_path: Path, config: dict | None = None) -> CheckResult:
        # Find split files
        splits_dir = dataset_path / "splits"
        if not splits_dir.exists():
            return CheckResult(
                check_name=self.name,
                status=CheckStatus.SKIPPED,
                message="No splits directory found",
            )

        split_files = list(splits_dir.glob("*.csv")) + list(splits_dir.glob("*.parquet"))

        if len(split_files) < 2:
            return CheckResult(
                check_name=self.name,
                status=CheckStatus.SKIPPED,
                message="Need at least 2 splits to check consistency",
            )

        # Load first split as reference
        first_file = split_files[0]
        if first_file.suffix == ".csv":
            ref_df = pl.read_csv(first_file)
        else:
            ref_df = pl.read_parquet(first_file)

        ref_columns = set(ref_df.columns)
        ref_schema = {col: ref_df[col].dtype for col in ref_df.columns}

        issues = []
        consistent = True

        for split_file in split_files[1:]:
            if split_file.suffix == ".csv":
                df = pl.read_csv(split_file)
            else:
                df = pl.read_parquet(split_file)

            # Check columns
            split_columns = set(df.columns)
            if split_columns != ref_columns:
                missing = ref_columns - split_columns
                extra = split_columns - ref_columns
                issues.append({
                    "file": split_file.name,
                    "issue": "Column mismatch",
                    "missing": list(missing),
                    "extra": list(extra),
                })
                consistent = False

            # Check types
            for col in df.columns:
                if col in ref_schema and df[col].dtype != ref_schema[col]:
                    issues.append({
                        "file": split_file.name,
                        "issue": "Type mismatch",
                        "column": col,
                        "expected": str(ref_schema[col]),
                        "actual": str(df[col].dtype),
                    })
                    consistent = False

        if not consistent:
            return CheckResult(
                check_name=self.name,
                status=CheckStatus.FAILED,
                severity=CheckSeverity.ERROR,
                message="Schema inconsistency detected",
                details={
                    "reference_file": first_file.name,
                    "issues": issues,
                },
                suggestions=["Ensure all splits have the same schema"],
            )

        return CheckResult(
            check_name=self.name,
            status=CheckStatus.PASSED,
            message="Schema is consistent across splits",
            details={
                "reference_file": first_file.name,
                "columns": list(ref_columns),
            },
        )
