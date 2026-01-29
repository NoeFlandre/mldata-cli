"""Export service for dataset export."""

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import polars as pl


@dataclass
class CompressionOptions:
    """Compression configuration options."""
    type: str
    level: int | None = None  # None means default/auto

    def __post_init__(self):
        """Validate compression level."""
        if self.level is not None:
            if self.type in ("gzip", "zstd"):
                if not 1 <= self.level <= 22:
                    raise ValueError(f"Compression level for {self.type} must be between 1 and 22")
            elif self.type == "snappy":
                self.level = None  # snappy doesn't support levels


class ExportService:
    """Service for exporting datasets in various formats."""

    # Compression tradeoffs guide
    COMPRESSION_GUIDE = {
        "snappy": {
            "description": "Fastest compression, moderate size reduction",
            "level_support": False,
            "typical_ratio": "2-3x",
            "speed": "Fastest"
        },
        "gzip": {
            "description": "Balanced speed and compression",
            "level_support": True,
            "levels": "1 (fastest) to 9 (best)",
            "typical_ratio": "3-5x",
            "speed": "Medium"
        },
        "zstd": {
            "description": "Best compression ratio, good speed",
            "level_support": True,
            "levels": "1 (fastest) to 22 (best)",
            "typical_ratio": "4-7x",
            "speed": "Fast"
        },
        "lz4": {
            "description": "Very fast, lower compression",
            "level_support": False,
            "typical_ratio": "2x",
            "speed": "Very Fast"
        },
        None: {
            "description": "No compression, fastest write speed",
            "level_support": False,
            "typical_ratio": "1x",
            "speed": "Instant"
        },
    }

    # Supported formats
    SUPPORTED_FORMATS = {"parquet", "csv", "json", "jsonl"}

    def __init__(self):
        """Initialize export service."""
        pass

    def parse_compression(self, compression: str | None) -> CompressionOptions:
        """Parse compression string into options.

        Args:
            compression: Compression string like "gzip:6" or "zstd"

        Returns:
            CompressionOptions instance
        """
        if compression is None:
            return CompressionOptions(type="snappy")

        if ":" in compression:
            comp_type, level_str = compression.rsplit(":", 1)
            try:
                level = int(level_str)
            except ValueError:
                raise ValueError(f"Invalid compression level: {level_str}")
            return CompressionOptions(type=comp_type, level=level)

        return CompressionOptions(type=compression)

    def parse_formats(self, formats: str | list[str]) -> list[str]:
        """Parse formats string or list into validated list.

        Args:
            formats: Comma-separated string or list of formats

        Returns:
            List of validated format strings
        """
        if isinstance(formats, str):
            format_list = [f.strip() for f in formats.split(",")]
        else:
            format_list = formats

        # Validate formats
        for fmt in format_list:
            if fmt.lower() not in self.SUPPORTED_FORMATS:
                raise ValueError(f"Unsupported format: {fmt}. Supported: {self.SUPPORTED_FORMATS}")

        return [f.lower() for f in format_list]

    def export(
        self,
        df: pl.DataFrame,
        output_path: Path,
        format: str = "parquet",
        compression: str | None = None,
    ) -> Path:
        """Export DataFrame to file.

        Args:
            df: Polars DataFrame
            output_path: Output file path
            format: Output format (parquet, csv, json, jsonl)
            compression: Compression type with optional level (e.g., "gzip:6", "zstd:3")

        Returns:
            Path to exported file
        """
        if format == "parquet":
            comp_options = self.parse_compression(compression)
            compression_map = {
                "snappy": "snappy",
                "gzip": "gzip",
                "zstd": "zstd",
                "lz4": "lz4",
                None: None,
            }
            comp = compression_map.get(comp_options.type, "snappy")

            # Write with compression and level if supported
            if comp_options.level is not None and comp in ("gzip", "zstd"):
                df.write_parquet(output_path, compression=comp, compression_level=comp_options.level)
            else:
                df.write_parquet(output_path, compression=comp)

        elif format == "csv":
            df.write_csv(output_path)

        elif format == "json":
            df.write_json(output_path)

        elif format == "jsonl":
            df.write_ndjson(output_path)

        else:
            raise ValueError(f"Unsupported format: {format}")

        return output_path

    def export_multiple(
        self,
        df: pl.DataFrame,
        output_dir: Path,
        formats: list[str] | None = None,
        compression: str | None = None,
    ) -> dict[str, Path]:
        """Export DataFrame to multiple formats.

        Args:
            df: Polars DataFrame
            output_dir: Output directory
            formats: List of formats to export
            compression: Compression type with optional level

        Returns:
            Dict mapping format to output path
        """
        if formats is None:
            formats = ["parquet"]

        output_paths = {}

        for fmt in formats:
            output_path = output_dir / f"data.{fmt}"
            output_paths[fmt] = self.export(df, output_path, format=fmt, compression=compression)

        return output_paths

    def export_all_formats(
        self,
        df: pl.DataFrame,
        output_dir: Path,
        compression: str | None = None,
    ) -> dict[str, Path]:
        """Export DataFrame to all supported formats.

        Args:
            df: Polars DataFrame
            output_dir: Output directory
            compression: Compression type with optional level

        Returns:
            Dict mapping format to output path
        """
        return self.export_multiple(
            df,
            output_dir,
            formats=list(self.SUPPORTED_FORMATS),
            compression=compression,
        )

    def export_splits(
        self,
        splits: dict[str, pl.DataFrame],
        output_dir: Path,
        format: str = "parquet",
        compression: str | None = None,
    ) -> dict[str, dict[str, Path]]:
        """Export split DataFrames to files.

        Args:
            splits: Dict of split name to DataFrame
            output_dir: Output directory
            format: Output format
            compression: Compression type with optional level

        Returns:
            Dict mapping split name to dict of format to path
        """
        split_outputs = {}

        for split_name, df in splits.items():
            split_dir = output_dir / split_name
            split_dir.mkdir(parents=True, exist_ok=True)

            output_paths = self.export_multiple(df, split_dir, [format], compression)
            split_outputs[split_name] = output_paths

        return split_outputs

    def export_splits_multiple(
        self,
        splits: dict[str, pl.DataFrame],
        output_dir: Path,
        formats: list[str] | None = None,
        compression: str | None = None,
    ) -> dict[str, dict[str, Path]]:
        """Export split DataFrames to multiple formats.

        Args:
            splits: Dict of split name to DataFrame
            output_dir: Output directory
            formats: List of formats to export
            compression: Compression type with optional level

        Returns:
            Dict mapping split name to dict of format to path
        """
        if formats is None:
            formats = ["parquet"]

        split_outputs = {}

        for split_name, df in splits.items():
            split_dir = output_dir / split_name
            split_dir.mkdir(parents=True, exist_ok=True)

            output_paths = self.export_multiple(df, split_dir, formats, compression)
            split_outputs[split_name] = output_paths

        return split_outputs

    def get_compression_info(self, compression: str | None) -> dict:
        """Get information about a compression option.

        Args:
            compression: Compression type (with optional level)

        Returns:
            Dict with compression information
        """
        comp_options = self.parse_compression(compression)
        info = self.COMPRESSION_GUIDE.get(comp_options.type, {}).copy()
        info["type"] = comp_options.type
        info["level"] = comp_options.level
        return info
