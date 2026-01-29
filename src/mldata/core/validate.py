"""Validation service for quality checks."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import polars as pl


@dataclass
class FileCheckResult:
    """Result of file integrity check."""
    path: Path
    file_type: str  # "image", "audio", "tabular"
    is_valid: bool
    error: str | None = None
    details: dict | None = None

    def __post_init__(self):
        if self.details is None:
            self.details = {}


class FileIntegrityService:
    """Service for validating file integrity (images, audio, etc.)."""

    # Supported image formats
    IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".tiff", ".tif"}

    # Supported audio formats
    AUDIO_EXTENSIONS = {".wav", ".mp3", ".flac", ".ogg", ".m4a", ".aac"}

    def __init__(self):
        """Initialize file integrity service."""
        pass

    def detect_file_type(self, path: Path) -> str:
        """Detect the type of a file.

        Args:
            path: Path to file

        Returns:
            File type string: "image", "audio", "tabular", or "unknown"
        """
        suffix = path.suffix.lower()

        if suffix in self.IMAGE_EXTENSIONS:
            return "image"
        elif suffix in self.AUDIO_EXTENSIONS:
            return "audio"
        elif suffix in {".csv", ".parquet", ".json", ".jsonl", ".arrow"}:
            return "tabular"
        else:
            return "unknown"

    def validate_image(self, path: Path) -> FileCheckResult:
        """Validate an image file.

        Args:
            path: Path to image file

        Returns:
            FileCheckResult with validation status
        """
        try:
            from PIL import Image

            with Image.open(path) as img:
                width, height = img.size
                format_name = img.format

                # Check for valid dimensions
                if width < 1 or height < 1:
                    return FileCheckResult(
                        path=path,
                        file_type="image",
                        is_valid=False,
                        error="Invalid image dimensions",
                        details={"width": width, "height": height},
                    )

                # Try to load the image data
                img.load()

                return FileCheckResult(
                    path=path,
                    file_type="image",
                    is_valid=True,
                    details={
                        "width": width,
                        "height": height,
                        "format": format_name,
                        "mode": img.mode,
                    },
                )

        except Exception as e:
            return FileCheckResult(
                path=path,
                file_type="image",
                is_valid=False,
                error=str(e),
            )

    def validate_audio(self, path: Path) -> FileCheckResult:
        """Validate an audio file.

        Args:
            path: Path to audio file

        Returns:
            FileCheckResult with validation status
        """
        try:
            import audiofile

            # Read audio file info
            info = audiofile.info(path)
            duration = info.duration
            sample_rate = info.samplerate
            channels = info.channels

            # Verify we can read the file
            signal, sr = audiofile.read(path, duration=0.1)  # Read 100ms sample

            return FileCheckResult(
                path=path,
                file_type="audio",
                is_valid=True,
                details={
                    "duration": duration,
                    "sample_rate": sample_rate,
                    "channels": channels,
                },
            )

        except Exception as e:
            return FileCheckResult(
                path=path,
                file_type="audio",
                is_valid=False,
                error=str(e),
            )

    def validate_file(self, path: Path) -> FileCheckResult:
        """Validate a single file.

        Args:
            path: Path to file

        Returns:
            FileCheckResult with validation status
        """
        if not path.exists():
            return FileCheckResult(
                path=path,
                file_type="unknown",
                is_valid=False,
                error="File not found",
            )

        file_type = self.detect_file_type(path)

        if file_type == "image":
            return self.validate_image(path)
        elif file_type == "audio":
            return self.validate_audio(path)
        elif file_type == "tabular":
            return FileCheckResult(
                path=path,
                file_type="tabular",
                is_valid=True,
                details={"message": "Tabular file - structural validation recommended"},
            )
        else:
            return FileCheckResult(
                path=path,
                file_type="unknown",
                is_valid=True,  # Unknown files are not errors
                details={"message": "Unknown file type - skipping validation"},
            )

    def run_checks(
        self,
        paths: list[Path],
        sample_percent: float = 100.0,
    ) -> list[FileCheckResult]:
        """Run file integrity checks on multiple files.

        Args:
            paths: List of file paths to check
            sample_percent: Percentage of files to check (for large datasets)

        Returns:
            List of FileCheckResult objects
        """
        import math

        results = []

        # If sampling, select files
        if sample_percent < 100.0:
            sample_count = max(1, math.ceil(len(paths) * sample_percent / 100))
            import random

            paths = random.sample(paths, min(sample_count, len(paths)))

        for path in paths:
            result = self.validate_file(path)
            results.append(result)

        return results


class ValidateService:
    """Service for validating dataset quality."""

    def __init__(self):
        """Initialize validation service."""
        pass

    def check_duplicates(self, df: pl.DataFrame, columns: list[str] | None = None) -> dict[str, Any]:
        """Check for duplicate rows.

        Args:
            df: Polars DataFrame
            columns: Columns to check (None for all)

        Returns:
            Check result dict
        """
        if columns is None:
            columns = df.columns

        # Exact duplicates
        total_rows = len(df)
        unique_rows = df.unique(subset=columns).height
        exact_duplicates = total_rows - unique_rows

        return {
            "check_name": "duplicates",
            "passed": exact_duplicates == 0,
            "exact_duplicates": exact_duplicates,
            "duplicate_ratio": exact_duplicates / total_rows if total_rows > 0 else 0,
        }

    def check_label_distribution(
        self,
        df: pl.DataFrame,
        label_column: str,
        imbalance_threshold: float = 0.1,
    ) -> dict[str, Any]:
        """Check label distribution for class imbalance.

        Args:
            df: Polars DataFrame
            label_column: Column containing labels
            imbalance_threshold: Threshold for imbalance warning

        Returns:
            Check result dict
        """
        if label_column not in df.columns:
            return {
                "check_name": "label_distribution",
                "passed": True,
                "message": f"Label column '{label_column}' not found",
            }

        label_counts = df.group_by(label_column).agg(pl.len().alias("count"))
        total = label_counts["count"].sum()

        if total == 0:
            return {
                "check_name": "label_distribution",
                "passed": True,
                "message": "No labeled samples found",
            }

        # Calculate distribution
        distribution = {}
        for row in label_counts.rows():
            label, count = row
            distribution[str(label)] = count / total

        # Find imbalance ratio
        counts = label_counts["count"].to_list()
        if counts:
            imbalance = (max(counts) - min(counts)) / total if max(counts) > min(counts) else 0
        else:
            imbalance = 0

        return {
            "check_name": "label_distribution",
            "passed": imbalance <= imbalance_threshold,
            "imbalance_ratio": imbalance,
            "distribution": distribution,
            "num_classes": len(counts),
        }

    def check_missing_values(
        self,
        df: pl.DataFrame,
        max_missing_ratio: float = 0.05,
    ) -> dict[str, Any]:
        """Check for missing values.

        Args:
            df: Polars DataFrame
            max_missing_ratio: Maximum acceptable missing ratio per column

        Returns:
            Check result dict
        """
        total_rows = len(df)
        issues = []

        for col_name in df.columns:
            missing_count = df[col_name].null_count()
            missing_ratio = missing_count / total_rows if total_rows > 0 else 0

            if missing_ratio > max_missing_ratio:
                issues.append({
                    "column": col_name,
                    "missing_count": missing_count,
                    "missing_ratio": missing_ratio,
                })

        return {
            "check_name": "missing_values",
            "passed": len(issues) == 0,
            "issues": issues,
            "total_missing": sum(i["missing_count"] for i in issues),
        }

    def check_schema_consistency(
        self,
        df: pl.DataFrame,
    ) -> dict[str, Any]:
        """Check schema consistency.

        Args:
            df: Polars DataFrame

        Returns:
            Check result dict
        """
        # Check for type consistency
        type_issues = []

        for col_name in df.columns:
            col_dtype = df[col_name].dtype
            # Check if column has mixed types
            if col_dtype == pl.Object:
                type_issues.append({
                    "column": col_name,
                    "issue": "Object type may contain mixed types",
                })

        return {
            "check_name": "schema_consistency",
            "passed": len(type_issues) == 0,
            "issues": type_issues,
            "num_columns": len(df.columns),
        }
