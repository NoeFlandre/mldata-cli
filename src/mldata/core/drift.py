"""Drift detection service for monitoring data distribution changes."""

from datetime import datetime
from enum import Enum
from pathlib import Path

import numpy as np
import polars as pl
from pydantic import BaseModel, Field


class DriftSeverity(str, Enum):
    """Severity level of drift."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class NumericDrift(BaseModel):
    """Drift metrics for numeric columns."""

    column: str
    psi: float | None = None
    kl_divergence: float | None = None
    drift_detected: bool = False
    severity: DriftSeverity = DriftSeverity.LOW
    baseline_stats: dict[str, float] = Field(default_factory=dict)
    current_stats: dict[str, float] = Field(default_factory=dict)


class CategoricalDrift(BaseModel):
    """Drift metrics for categorical columns."""

    column: str
    psi: float | None = None
    chi_squared: float | None = None
    drift_detected: bool = False
    severity: DriftSeverity = DriftSeverity.LOW
    baseline_distribution: dict[str, float] = Field(default_factory=dict)
    current_distribution: dict[str, float] = Field(default_factory=dict)


class DriftReport(BaseModel):
    """Full drift detection report."""

    version: str = "1.0"
    generated_at: datetime
    baseline_path: str
    current_path: str
    baseline_samples: int = 0
    current_samples: int = 0
    numeric_drift: dict[str, dict] = Field(default_factory=dict)
    categorical_drift: dict[str, dict] = Field(default_factory=dict)
    overall_drift_detected: bool = False
    severity_summary: dict[str, int] = Field(default_factory=dict)

    def to_json(self, path: str) -> None:
        """Export report to JSON."""
        import json

        with open(path, "w") as f:
            json.dump(self.model_dump(mode="json"), f, indent=2)

    def to_markdown(self, path: str | None = None) -> str:
        """Generate markdown report.

        Args:
            path: Optional path to write file

        Returns:
            Markdown string
        """
        lines = [
            "# Drift Detection Report",
            f"**Generated:** {self.generated_at.isoformat()}",
            "",
            "## Overview",
            f"- Baseline: {self.baseline_path}",
            f"- Current: {self.current_path}",
            f"- Baseline samples: {self.baseline_samples:,}",
            f"- Current samples: {self.current_samples:,}",
            f"- Overall drift detected: {'Yes' if self.overall_drift_detected else 'No'}",
            "",
            "## Severity Summary",
            f"- Low severity: {self.severity_summary.get('low', 0)}",
            f"- Medium severity: {self.severity_summary.get('medium', 0)}",
            f"- High severity: {self.severity_summary.get('high', 0)}",
            "",
        ]

        if self.numeric_drift:
            lines.append("## Numeric Drift")
            lines.append("")
            for col, drift in self.numeric_drift.items():
                status = "DRIFT" if drift.get("drift_detected") else "OK"
                lines.append(f"### {col} ({status})")
                lines.append(f"- PSI: {drift.get('psi', 'N/A'):.4f}" if drift.get("psi") else "- PSI: N/A")
                lines.append(f"- Severity: {drift.get('severity', 'unknown')}")
                lines.append("")

        if self.categorical_drift:
            lines.append("## Categorical Drift")
            lines.append("")
            for col, drift in self.categorical_drift.items():
                status = "DRIFT" if drift.get("drift_detected") else "OK"
                chi_sq = f"{drift.get('chi_squared', 'N/A'):.4f}" if drift.get("chi_squared") else "N/A"
                lines.append(f"### {col} ({status})")
                lines.append(f"- Chi-squared: {chi_sq}")
                lines.append(f"- Severity: {drift.get('severity', 'unknown')}")
                lines.append("")

        output = "\n".join(lines)

        if path:
            with open(path, "w") as f:
                f.write(output)

        return output


class DriftService:
    """Service for detecting data drift between datasets."""

    PSI_THRESHOLD_LOW = 0.05
    PSI_THRESHOLD_MEDIUM = 0.1
    PSI_THRESHOLD_HIGH = 0.25

    def __init__(self, psi_bins: int = 10):
        """Initialize drift service.

        Args:
            psi_bins: Number of bins for PSI calculation
        """
        self.psi_bins = psi_bins

    def compute_psi(
        self,
        baseline: list[float],
        current: list[float],
        bins: int | None = None,
    ) -> float:
        """Compute Population Stability Index (PSI).

        PSI = sum((actual% - expected%) * ln(actual% / expected%))

        Args:
            baseline: Baseline distribution values
            current: Current distribution values
            bins: Number of bins (default: self.psi_bins)

        Returns:
            PSI value
        """
        if not baseline or not current:
            return 0.0

        bins = bins or self.psi_bins

        # Create bins based on baseline
        baseline_arr = np.array(baseline)
        current_arr = np.array(current)

        # Handle edge cases
        if len(baseline_arr) == 0 or len(current_arr) == 0:
            return 0.0

        # Calculate bin edges
        min_val = min(baseline_arr.min(), current_arr.min())
        max_val = max(baseline_arr.max(), current_arr.max())

        if min_val == max_val:
            return 0.0

        # Create bins
        bin_edges = np.linspace(min_val, max_val, bins + 1)

        # Calculate bin percentages for baseline
        baseline_counts, _ = np.histogram(baseline_arr, bins=bin_edges)
        baseline_pct = baseline_counts / len(baseline_arr)

        # Calculate bin percentages for current
        current_counts, _ = np.histogram(current_arr, bins=bin_edges)
        current_pct = current_counts / len(current_arr)

        # Add small epsilon to avoid log(0)
        baseline_pct = np.clip(baseline_pct, 1e-10, 1.0)
        current_pct = np.clip(current_pct, 1e-10, 1.0)

        # Calculate PSI
        psi = np.sum((current_pct - baseline_pct) * np.log(current_pct / baseline_pct))

        return float(psi)

    def compute_kl_divergence(
        self,
        p: list[float] | np.ndarray,
        q: list[float] | np.ndarray,
    ) -> float:
        """Compute KL Divergence D(P || Q).

        KL = sum(P[i] * log(P[i] / Q[i]))

        Args:
            p: Baseline distribution (must sum to 1)
            q: Current distribution (must sum to 1)

        Returns:
            KL divergence value
        """
        p = np.asarray(p)
        q = np.asarray(q)

        # Normalize to ensure they sum to 1
        p = p / p.sum() if p.sum() > 0 else p
        q = q / q.sum() if q.sum() > 0 else q

        # Add small epsilon to avoid log(0)
        p = np.clip(p, 1e-10, 1.0)
        q = np.clip(q, 1e-10, 1.0)

        return float(np.sum(p * np.log(p / q)))

    def compute_chi_squared(
        self,
        baseline_counts: list[int] | np.ndarray,
        current_counts: list[int] | np.ndarray,
    ) -> float:
        """Compute chi-squared statistic for categorical distributions.

        Args:
            baseline_counts: Counts in each category for baseline
            current_counts: Counts in each category for current

        Returns:
            Chi-squared statistic
        """
        baseline_counts = np.array(baseline_counts)
        current_counts = np.array(current_counts)

        if len(baseline_counts) == 0 or len(current_counts) == 0:
            return 0.0

        # Calculate expected frequencies
        total_baseline = baseline_counts.sum()
        total_current = current_counts.sum()

        if total_baseline == 0 or total_current == 0:
            return 0.0

        # Calculate proportions
        p_baseline = baseline_counts / total_baseline
        expected = p_baseline * total_current

        # Avoid division by zero
        expected = np.clip(expected, 1e-10, None)

        # Chi-squared
        chi_squared = ((current_counts - expected) ** 2 / expected).sum()

        return float(chi_squared)

    def _psi_to_severity(self, psi: float) -> DriftSeverity:
        """Convert PSI value to severity level."""
        if psi < self.PSI_THRESHOLD_LOW:
            return DriftSeverity.LOW
        elif psi < self.PSI_THRESHOLD_MEDIUM:
            return DriftSeverity.MEDIUM
        else:
            return DriftSeverity.HIGH

    def _kl_to_severity(self, kl: float) -> DriftSeverity:
        """Convert KL divergence to severity level."""
        if kl < 0.1:
            return DriftSeverity.LOW
        elif kl < 0.5:
            return DriftSeverity.MEDIUM
        else:
            return DriftSeverity.HIGH

    def detect_drift(
        self,
        baseline_path: Path,
        current_path: Path,
    ) -> DriftReport:
        """Detect drift between two datasets.

        Args:
            baseline_path: Path to baseline dataset
            current_path: Path to current dataset

        Returns:
            DriftReport with all drift metrics
        """
        from mldata.core.normalize import NormalizeService

        normalize = NormalizeService()

        # Read data
        baseline_df = normalize.read_data(baseline_path)
        current_df = normalize.read_data(current_path)

        report = DriftReport(
            generated_at=datetime.now(),
            baseline_path=str(baseline_path),
            current_path=str(current_path),
            baseline_samples=len(baseline_df),
            current_samples=len(current_df),
        )

        numeric_dtypes = {
            pl.Float64,
            pl.Float32,
            pl.Int64,
            pl.Int32,
            pl.Int16,
            pl.Int8,
            pl.UInt64,
            pl.UInt32,
            pl.UInt16,
            pl.UInt8,
        }

        severity_counts = {"low": 0, "medium": 0, "high": 0}
        any_drift = False

        # Check numeric columns
        for col in baseline_df.columns:
            baseline_col = baseline_df[col]
            current_col = current_df[col]

            if baseline_col.dtype in numeric_dtypes:
                baseline_vals = baseline_col.drop_nulls().to_list()
                current_vals = current_col.drop_nulls().to_list()

                if len(baseline_vals) > 0 and len(current_vals) > 0:
                    psi = self.compute_psi(baseline_vals, current_vals)
                    severity = self._psi_to_severity(float(psi))
                    drift_detected = psi >= self.PSI_THRESHOLD_MEDIUM

                    if drift_detected:
                        any_drift = True
                        severity_counts[severity.value] += 1

                    report.numeric_drift[col] = {
                        "psi": psi,
                        "drift_detected": drift_detected,
                        "severity": severity.value,
                        "baseline_stats": {
                            "mean": float(np.mean(baseline_vals)),
                            "std": float(np.std(baseline_vals)) if len(baseline_vals) > 1 else 0,
                            "min": float(np.min(baseline_vals)),
                            "max": float(np.max(baseline_vals)),
                        },
                        "current_stats": {
                            "mean": float(np.mean(current_vals)),
                            "std": float(np.std(current_vals)) if len(current_vals) > 1 else 0,
                            "min": float(np.min(current_vals)),
                            "max": float(np.max(current_vals)),
                        },
                    }

        # Check categorical columns
        for col in baseline_df.columns:
            baseline_col = baseline_df[col]
            current_col = current_df[col]

            if baseline_col.dtype == pl.Utf8:
                baseline_counts = baseline_col.value_counts()["count"].to_list()
                current_counts = current_col.value_counts()["count"].to_list()

                # Pad to same length if needed
                max_len = max(len(baseline_counts), len(current_counts))
                baseline_counts.extend([0] * (max_len - len(baseline_counts)))
                current_counts.extend([0] * (max_len - len(current_counts)))

                if sum(baseline_counts) > 0 and sum(current_counts) > 0:
                    chi_sq = self.compute_chi_squared(np.array(baseline_counts), np.array(current_counts))

                    # Normalize to get approximate PSI-like metric
                    p_baseline = np.array(baseline_counts) / sum(baseline_counts)
                    p_current = np.array(current_counts) / sum(current_counts)
                    p_baseline = np.clip(p_baseline, 1e-10, 1.0)
                    p_current = np.clip(p_current, 1e-10, 1.0)
                    psi = np.sum((p_current - p_baseline) * np.log(p_current / p_baseline))

                    severity = self._psi_to_severity(abs(psi))
                    drift_detected = abs(psi) >= self.PSI_THRESHOLD_MEDIUM

                    if drift_detected:
                        any_drift = True
                        severity_counts[severity.value] += 1

                    report.categorical_drift[col] = {
                        "psi": abs(psi),
                        "chi_squared": chi_sq,
                        "drift_detected": drift_detected,
                        "severity": severity.value,
                    }

        report.overall_drift_detected = any_drift
        report.severity_summary = severity_counts

        return report
