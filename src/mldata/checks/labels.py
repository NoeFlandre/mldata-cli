"""Label distribution check."""

from pathlib import Path
from typing import Any

import polars as pl

from mldata.checks.base import BaseCheck, CheckResult, CheckStatus, CheckSeverity


class LabelDistributionCheck(BaseCheck):
    """Check for label distribution imbalances."""

    name = "label_distribution"
    description = "Analyze class label distribution"

    @property
    def configurable_params(self) -> dict:
        return {
            "label_column": None,
            "imbalance_threshold": 0.1,
        }

    def run(self, dataset_path: Path, config: dict | None = None) -> CheckResult:
        config = config or {}
        label_column = config.get("label_column")
        imbalance_threshold = config.get("imbalance_threshold", 0.1)

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

        # Auto-detect label column if not specified
        if label_column is None:
            label_candidates = ["label", "class", "target", "category"]
            for candidate in label_candidates:
                if candidate in df.columns:
                    label_column = candidate
                    break

        if label_column is None or label_column not in df.columns:
            return CheckResult(
                check_name=self.name,
                status=CheckStatus.SKIPPED,
                message=f"Label column '{label_column}' not found",
            )

        # Calculate distribution
        label_counts = df.group_by(label_column).agg(pl.count().alias("count"))
        total = label_counts["count"].sum()

        if total == 0:
            return CheckResult(
                check_name=self.name,
                status=CheckStatus.PASSED,
                message="No labeled samples found",
            )

        distribution = {}
        for row in label_counts.rows():
            label, count = row
            distribution[str(label)] = count / total

        # Calculate imbalance
        counts = label_counts["count"].to_list()
        if counts:
            imbalance = (max(counts) - min(counts)) / total
        else:
            imbalance = 0

        if imbalance > imbalance_threshold:
            return CheckResult(
                check_name=self.name,
                status=CheckStatus.FAILED,
                severity=CheckSeverity.WARNING,
                message=f"Class imbalance detected (ratio: {imbalance:.2%})",
                details={
                    "distribution": distribution,
                    "imbalance_ratio": imbalance,
                    "num_classes": len(counts),
                },
                suggestions=[
                    "Consider using stratified splitting",
                    "Apply class weights during training",
                ],
            )

        return CheckResult(
            check_name=self.name,
            status=CheckStatus.PASSED,
            message="Label distribution is balanced",
            details={
                "distribution": distribution,
                "imbalance_ratio": imbalance,
            },
        )
