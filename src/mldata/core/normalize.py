"""Normalization service for format conversion and schema handling."""

from pathlib import Path
from typing import Any

import polars as pl


class NormalizeService:
    """Service for normalizing datasets to standard formats."""

    def __init__(self):
        """Initialize normalization service."""
        pass

    def detect_format(self, file_path: Path) -> str:
        """Detect the format of a data file.

        Args:
            file_path: Path to data file

        Returns:
            Detected format (csv, json, jsonl, parquet)
        """
        suffix = file_path.suffix.lower()

        format_map = {
            ".csv": "csv",
            ".json": "json",
            ".jsonl": "jsonl",
            ".parquet": "parquet",
            ".arrow": "arrow",
        }

        return format_map.get(suffix, "unknown")

    def read_data(self, file_path: Path) -> pl.DataFrame:
        """Read data file into Polars DataFrame.

        Args:
            file_path: Path to data file

        Returns:
            Polars DataFrame
        """
        format_type = self.detect_format(file_path)

        if format_type == "csv":
            return pl.read_csv(file_path)
        elif format_type == "json":
            return pl.read_json(file_path)
        elif format_type == "jsonl":
            return pl.read_ndjson(file_path)
        elif format_type == "parquet":
            return pl.read_parquet(file_path)
        else:
            raise ValueError(f"Unsupported format: {format_type}")

    def convert_format(
        self,
        input_path: Path,
        output_path: Path,
        target_format: str,
        compression: str | None = None,
    ) -> Path:
        """Convert data to target format.

        Args:
            input_path: Input file path
            output_path: Output file path
            target_format: Target format (csv, json, jsonl, parquet)
            compression: Compression type for output

        Returns:
            Path to converted file
        """
        df = self.read_data(input_path)

        if target_format == "csv":
            df.write_csv(output_path)
        elif target_format == "json":
            df.write_json(output_path)
        elif target_format == "jsonl":
            df.write_ndjson(output_path)
        elif target_format == "parquet":
            compression_map = {
                "snappy": "snappy",
                "gzip": "gzip",
                "zstd": "zstd",
            }
            comp = compression_map.get(compression, "snappy")
            df.write_parquet(output_path, compression=comp)
        else:
            raise ValueError(f"Unsupported format: {target_format}")

        return output_path

    def infer_schema(self, df: pl.DataFrame) -> list[dict[str, Any]]:
        """Infer schema from DataFrame.

        Args:
            df: Polars DataFrame

        Returns:
            List of column information dicts
        """
        schema = []
        for col_name in df.columns:
            col_dtype = df[col_name].dtype
            nullable = df[col_name].null_count() > 0

            schema.append(
                {
                    "name": col_name,
                    "dtype": str(col_dtype),
                    "nullable": nullable,
                }
            )

        return schema

    def create_standard_layout(self, output_dir: Path, dataset_name: str) -> dict[str, Path]:
        """Create standard directory layout for dataset.

        Args:
            output_dir: Base output directory
            dataset_name: Name of the dataset

        Returns:
            Dict mapping section names to paths
        """
        dataset_dir = output_dir / dataset_name
        layout = {
            "root": dataset_dir,
            "manifest": dataset_dir / "manifest.yaml",
            "reports": dataset_dir / "reports",
            "splits": dataset_dir / "splits",
            "artifacts": dataset_dir / "artifacts",
            "raw": dataset_dir / "raw",
            "intermediate": dataset_dir / "intermediate",
        }

        for path in layout.values():
            path.mkdir(parents=True, exist_ok=True)

        return layout
