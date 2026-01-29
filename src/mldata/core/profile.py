"""Profile service for dataset statistics and analysis."""

from datetime import datetime
from pathlib import Path
from typing import Any

import polars as pl
from pydantic import BaseModel, Field


class ColumnProfile(BaseModel):
    """Profile for a single column."""

    name: str
    dtype: str
    nullable: bool = False
    unique_count: int | None = None
    null_count: int | None = None
    null_ratio: float | None = None


class NumericStats(BaseModel):
    """Statistics for numeric columns."""

    mean: float | None = None
    std: float | None = None
    min: float | None = None
    max: float | None = None
    median: float | None = None
    percentiles: dict[str, float] = Field(default_factory=dict)


class CategoricalStats(BaseModel):
    """Statistics for categorical columns."""

    unique_values: int | None = None
    top_values: list[dict[str, Any]] = Field(default_factory=list)


class DatasetProfile(BaseModel):
    """Full profile of a dataset."""

    version: str = "1.0"
    generated_at: datetime
    path: str
    file_size_bytes: int | None = None
    num_rows: int | None = None
    num_columns: int | None = None
    columns: list[ColumnProfile] = Field(default_factory=list)
    numeric_stats: dict[str, NumericStats] = Field(default_factory=dict)
    categorical_stats: dict[str, CategoricalStats] = Field(default_factory=dict)

    def to_json(self, path: str) -> None:
        """Export profile to JSON file."""
        import json

        with open(path, "w") as f:
            json.dump(self.model_dump(mode="json"), f, indent=2)

    def to_markdown(self, path: str | None = None) -> str:
        """Generate markdown summary of profile.

        Args:
            path: Optional path to write file

        Returns:
            Markdown string
        """
        lines = [
            "# Dataset Profile",
            f"**Generated:** {self.generated_at.isoformat()}",
            f"**Path:** {self.path}",
            "",
            "## Overview",
            f"- Rows: {self.num_rows:,}" if self.num_rows else "- Rows: Unknown",
            f"- Columns: {self.num_columns}" if self.num_columns else "- Columns: Unknown",
            f"- File Size: {self.file_size_bytes / 1024 / 1024:.2f} MB" if self.file_size_bytes else "",
            "",
            "## Schema",
        ]

        # Schema table
        lines.append("| # | Name | Type | Nullable | Unique |")
        lines.append("|---|------|------|----------|--------|")
        for i, col in enumerate(self.columns, 1):
            nullable = "Yes" if col.nullable else "No"
            unique = str(col.unique_count) if col.unique_count else "-"
            lines.append(f"| {i} | {col.name} | {col.dtype} | {nullable} | {unique} |")

        # Numeric statistics
        if self.numeric_stats:
            lines.append("")
            lines.append("## Numeric Statistics")
            lines.append("")
            for col_name, stats in self.numeric_stats.items():
                lines.append(f"### {col_name}")
                lines.append(f"- Mean: {stats.mean:.4f}" if stats.mean is not None else "- Mean: N/A")
                lines.append(f"- Std:  {stats.std:.4f}" if stats.std is not None else "- Std: N/A")
                lines.append(f"- Min:  {stats.min}" if stats.min is not None else "- Min: N/A")
                lines.append(f"- Max:  {stats.max}" if stats.max is not None else "- Max: N/A")
                lines.append(f"- Median: {stats.median}" if stats.median is not None else "- Median: N/A")
                if stats.percentiles:
                    lines.append("- Percentiles:")
                    for p, v in sorted(stats.percentiles.items()):
                        lines.append(f"  - {p}: {v:.4f}")
                lines.append("")

        # Categorical statistics
        if self.categorical_stats:
            lines.append("## Categorical Statistics")
            lines.append("")
            for col_name, stats in self.categorical_stats.items():
                lines.append(f"### {col_name}")
                lines.append(f"- Unique Values: {stats.unique_values}")
                if stats.top_values:
                    lines.append("- Top Values:")
                    for v in stats.top_values[:5]:
                        lines.append(f"  - {v['value']}: {v['count']:,}")
                lines.append("")

        output = "\n".join(lines)

        if path:
            with open(path, "w") as f:
                f.write(output)

        return output


class ProfileService:
    """Service for generating dataset profiles."""

    NUMERIC_DTYPES = {
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

    def __init__(self):
        """Initialize profile service."""
        pass

    def profile(self, path: Path) -> DatasetProfile:
        """Generate a full profile of a dataset.

        Args:
            path: Path to data file or directory

        Returns:
            DatasetProfile with all statistics
        """
        df = self._read_data(path)
        file_size = path.stat().st_size if path.exists() else None

        profile = DatasetProfile(
            generated_at=datetime.now(),
            path=str(path),
            file_size_bytes=file_size,
            num_rows=len(df),
            num_columns=len(df.columns),
        )

        # Profile each column
        for col_name in df.columns:
            col_profile = self._profile_column(df, col_name)
            profile.columns.append(col_profile)

            # Compute statistics
            if df[col_name].dtype in self.NUMERIC_DTYPES:
                profile.numeric_stats[col_name] = self._compute_numeric_stats(df, col_name)
            else:
                profile.categorical_stats[col_name] = self._compute_categorical_stats(df, col_name)

        return profile

    def _read_data(self, path: Path) -> pl.DataFrame:
        """Read data file into DataFrame."""
        from mldata.core.normalize import NormalizeService

        normalize = NormalizeService()

        if path.is_dir():
            # Find data files
            data_files = list(path.glob("*.parquet")) + list(path.glob("*.csv")) + list(path.glob("*.jsonl"))
            if not data_files:
                raise ValueError(f"No data files found in {path}")
            path = data_files[0]

        return normalize.read_data(path)

    def _profile_column(self, df: pl.DataFrame, col_name: str) -> ColumnProfile:
        """Profile a single column."""
        col = df[col_name]
        null_count = col.null_count()

        return ColumnProfile(
            name=col_name,
            dtype=str(col.dtype),
            nullable=null_count > 0,
            unique_count=col.n_unique(),
            null_count=int(null_count),
            null_ratio=float(null_count / len(df)) if len(df) > 0 else 0,
        )

    def _compute_numeric_stats(self, df: pl.DataFrame, col_name: str) -> NumericStats:
        """Compute statistics for numeric column."""
        col = df[col_name].drop_nulls()

        if len(col) == 0:
            return NumericStats()

        values = col.sort()

        # Compute percentiles
        percentiles = {}
        for p in [0.25, 0.5, 0.75, 0.9, 0.95, 0.99]:
            percentiles[f"{int(p * 100)}"] = float(values.quantile(p))

        return NumericStats(
            mean=float(col.mean()) if len(col) > 0 else None,
            std=float(col.std()) if len(col) > 1 else None,
            min=float(col.min()) if len(col) > 0 else None,
            max=float(col.max()) if len(col) > 0 else None,
            median=float(values.quantile(0.5)),
            percentiles=percentiles,
        )

    def _compute_categorical_stats(self, df: pl.DataFrame, col_name: str) -> CategoricalStats:
        """Compute statistics for categorical column."""
        col = df[col_name].drop_nulls()

        value_counts = col.value_counts().sort("count", descending=True)

        top_values = [{"value": row[col_name], "count": int(row["count"])} for row in value_counts.to_dicts()][:10]

        return CategoricalStats(
            unique_values=col.n_unique(),
            top_values=top_values,
        )

    def profile_directory(self, path: Path) -> dict[str, DatasetProfile]:
        """Profile all data files in a directory.

        Args:
            path: Path to directory

        Returns:
            Dict mapping filename to DatasetProfile
        """
        profiles = {}

        data_files = list(path.glob("*.parquet")) + list(path.glob("*.csv")) + list(path.glob("*.jsonl"))

        for data_file in data_files:
            try:
                profiles[data_file.name] = self.profile(data_file)
            except Exception:
                continue

        return profiles
