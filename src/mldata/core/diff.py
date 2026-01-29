"""Diff service for comparing datasets."""

from pathlib import Path
from typing import Any

import polars as pl


class DiffService:
    """Service for comparing datasets."""

    def __init__(self):
        """Initialize diff service."""
        pass

    def compare_data(
        self,
        path1: Path,
        path2: Path,
    ) -> dict[str, Any]:
        """Compare two dataset builds.

        Args:
            path1: Path to first dataset directory
            path2: Path to second dataset directory

        Returns:
            Comparison results dict
        """
        # Find data files
        data_files1 = self._find_data_files(path1)
        data_files2 = self._find_data_files(path2)

        if not data_files1 or not data_files2:
            return {
                "error": "Could not find data files in one or both paths",
                "path1_files": data_files1,
                "path2_files": data_files2,
            }

        # Load first file from each
        df1 = self._read_data(data_files1[0])
        df2 = self._read_data(data_files2[0])

        if df1 is None or df2 is None:
            return {"error": "Failed to read data files"}

        # Compare shapes
        shape_comparison = {
            "path1": {
                "rows": len(df1),
                "columns": len(df1.columns),
            },
            "path2": {
                "rows": len(df2),
                "columns": len(df2.columns),
            },
            "rows_match": len(df1) == len(df2),
            "columns_match": len(df1.columns) == len(df2.columns),
        }

        # Compare schemas
        schema_comparison = self._compare_schema(df1, df2)

        # Compare checksums
        checksum1 = self._compute_checksum(data_files1[0])
        checksum2 = self._compute_checksum(data_files2[0])

        # Compare sample values (first 5 rows)
        sample_comparison = self._compare_samples(df1, df2)

        return {
            "shape": shape_comparison,
            "schema": schema_comparison,
            "checksums": {
                "path1": checksum1,
                "path2": checksum2,
                "match": checksum1 == checksum2,
            },
            "sample_values": sample_comparison,
        }

    def _find_data_files(self, path: Path) -> list[Path]:
        """Find data files in directory."""
        if path.is_file():
            if path.suffix.lower() in (".csv", ".parquet", ".jsonl"):
                return [path]
            return []

        files = []
        for ext in [".parquet", ".csv", ".jsonl"]:
            files.extend(sorted(path.rglob(f"*{ext}")))
        return files

    def _read_data(self, path: Path) -> pl.DataFrame | None:
        """Read data file."""
        try:
            if path.suffix == ".parquet":
                return pl.read_parquet(path)
            elif path.suffix == ".csv":
                return pl.read_csv(path)
            elif path.suffix == ".jsonl":
                return pl.read_ndjson(path)
        except Exception:
            pass
        return None

    def _compare_schema(self, df1: pl.DataFrame, df2: pl.DataFrame) -> dict[str, Any]:
        """Compare schemas of two DataFrames."""
        cols1 = set(df1.columns)
        cols2 = set(df2.columns)

        common_cols = cols1 & cols2
        only_in_1 = cols1 - cols2
        only_in_2 = cols2 - cols1

        type_mismatches = []
        for col in common_cols:
            if col in df1.columns and col in df2.columns:
                dtype1 = df1[col].dtype
                dtype2 = df2[col].dtype
                if dtype1 != dtype2:
                    type_mismatches.append({
                        "column": col,
                        "type1": str(dtype1),
                        "type2": str(dtype2),
                    })

        return {
            "columns_match": cols1 == cols2,
            "common_columns": list(common_cols),
            "only_in_1": list(only_in_1),
            "only_in_2": list(only_in_2),
            "type_mismatches": type_mismatches,
            "all_types_match": len(type_mismatches) == 0,
        }

    def _compute_checksum(self, path: Path) -> str:
        """Compute checksum of file."""
        import hashlib

        sha256 = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        return sha256.hexdigest()[:16]  # First 16 chars

    def _compare_samples(self, df1: pl.DataFrame, df2: pl.DataFrame) -> dict[str, Any]:
        """Compare sample values."""
        sample1 = df1.head(5)
        sample2 = df2.head(5)

        column_comparisons = []
        for col in df1.columns:
            if col in df2.columns:
                vals1 = sample1[col].to_list()
                vals2 = sample2[col].to_list()
                match = vals1 == vals2
                column_comparisons.append({
                    "column": col,
                    "match": match,
                    "path1_values": vals1,
                    "path2_values": vals2,
                })

        return {
            "columns": column_comparisons,
            "all_match": all(c["match"] for c in column_comparisons),
        }
