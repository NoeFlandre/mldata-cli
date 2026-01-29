"""Local connector for local files and directories."""

import os
from pathlib import Path
from typing import Any, AsyncIterator

import polars as pl

from mldata.models.dataset import (
    ColumnInfo,
    DatasetMetadata,
    DatasetSource,
    DataFormat,
    DataModality,
    DownloadProgress,
    SearchResult,
)
from mldata.connectors.base import BaseConnector


class LocalConnector(BaseConnector):
    """Connector for local files and directories."""

    name = "local"
    uri_schemes = ["file://", "local://", None]  # None = bare path

    # Extensions supported for data files
    SUPPORTED_EXTENSIONS = {".csv", ".parquet", ".json", ".jsonl", ".arrow"}

    def parse_uri(self, uri: str) -> tuple[str, dict[str, str]]:
        """Parse local URI/file path.

        Formats supported:
        - file:///path/to/file.csv
        - /absolute/path/to/file.csv
        - ./relative/path/to/file.csv
        - relative/path/to/file.csv
        - data/*.csv (glob pattern)
        - data/ (directory)

        Args:
            uri: File path or URI

        Returns:
            Tuple of (path, params_dict)
        """
        params: dict[str, str] = {}

        # Handle file:// scheme
        if uri.startswith("file://"):
            path = uri[7:]
        # Handle local:// scheme (legacy)
        elif uri.startswith("local://"):
            path = uri[8:]
        # Relative or absolute path
        else:
            path = uri

        # Expand user home directory
        path = os.path.expanduser(path)

        return path, params

    def _detect_local_path(self, uri: str) -> tuple[str, dict[str, str]]:
        """Detect if URI is a local path.

        Args:
            uri: URI to check

        Returns:
            Tuple of (path, metadata_dict)
        """
        # Handle explicit schemes
        if uri.startswith("file://"):
            path = uri[7:]
            return path, {"scheme": "file"}
        if uri.startswith("local://"):
            path = uri[8:]
            return path, {"scheme": "local"}

        # Handle relative paths
        if uri.startswith("./") or uri.startswith("../"):
            return uri, {"scheme": "local"}

        # Check if it's a glob pattern
        if "*" in uri:
            return uri, {"scheme": "glob"}

        # Check if path exists
        path = Path(uri)
        if path.exists():
            return uri, {"scheme": "local"}
        if path.absolute().exists():
            return str(path.absolute()), {"scheme": "local"}

        raise ValueError(f"Local path not found: {uri}")

    async def authenticate(self) -> bool:
        """Local datasets don't need authentication."""
        return True

    async def search(
        self,
        query: str,
        *,
        limit: int = 20,
        modality: str | None = None,
        task: str | None = None,
    ) -> list[SearchResult]:
        """Search local directories is not supported.

        Args:
            query: Ignored
            limit: Ignored
            modality: Ignored
            task: Ignored

        Returns:
            Empty list - local search not supported
        """
        return []

    async def get_metadata(self, path: str) -> DatasetMetadata:
        """Get metadata for local file or directory.

        Args:
            path: Path to file or directory

        Returns:
            Dataset metadata with schema info
        """
        source_path = Path(path)

        if not source_path.exists():
            raise ValueError(f"Local path not found: {path}")

        # Handle glob patterns
        if "*" in str(path):
            return self._get_metadata_glob(path)

        if source_path.is_file():
            return self._get_metadata_file(source_path)

        # Directory - look for data files
        return self._get_metadata_directory(source_path)

    def _get_metadata_glob(self, pattern: str) -> DatasetMetadata:
        """Get metadata for glob pattern."""
        import glob as glob_module

        files = sorted(glob_module.glob(pattern))
        if not files:
            raise ValueError(f"No files found matching pattern: {pattern}")

        path = Path(files[0])
        return self._get_metadata_file(path)

    def _get_metadata_file(self, path: Path) -> DatasetMetadata:
        """Get metadata for a single file."""
        format_type = self._detect_format(path)

        # Get file size
        size_bytes = path.stat().st_size

        # Get schema and sample data
        columns: list[ColumnInfo] | None = None
        num_samples: int | None = None
        sample_rows: list[dict[str, Any]] | None = None
        num_columns: int | None = None

        try:
            if format_type in (DataFormat.CSV, DataFormat.PARQUET):
                df = pl.read_parquet(path) if format_type == DataFormat.PARQUET else pl.read_csv(path, n_rows=100)
                columns = self._extract_schema(df)
                num_samples = pl.read_parquet(path).height if format_type == DataFormat.PARQUET else None
                num_columns = len(df.columns)

                # Get sample rows
                sample_df = df.head(5)
                sample_rows = sample_df.to_dicts()
        except Exception:
            pass  # Keep None values on failure

        modality = self._infer_modality(path.name, columns)

        return DatasetMetadata(
            source=DatasetSource.LOCAL,
            dataset_id=str(path.absolute()),
            name=path.stem,
            description=f"Local file: {path.name}",
            size_bytes=size_bytes,
            num_samples=num_samples,
            num_columns=num_columns,
            columns=columns,
            modality=modality,
            tasks=[],
            url=f"file://{path.absolute()}",
        )

    def _get_metadata_directory(self, path: Path) -> DatasetMetadata:
        """Get metadata for a directory of files."""
        data_files = self._find_data_files(path)

        if not data_files:
            raise ValueError(f"No supported data files found in: {path}")

        # Get info from first file
        first_file = data_files[0]
        columns: list[ColumnInfo] | None = None
        num_columns: int | None = None
        num_samples: int | None = None

        try:
            format_type = self._detect_format(first_file)
            if format_type in (DataFormat.CSV, DataFormat.PARQUET):
                df = pl.read_parquet(first_file) if format_type == DataFormat.PARQUET else pl.read_csv(first_file, n_rows=100)
                columns = self._extract_schema(df)
                num_columns = len(df.columns)
                num_samples = pl.read_parquet(first_file).height if format_type == DataFormat.PARQUET else None
        except Exception:
            pass

        # Calculate total size
        total_size = sum(f.stat().st_size for f in data_files)

        return DatasetMetadata(
            source=DatasetSource.LOCAL,
            dataset_id=str(path.absolute()),
            name=path.name,
            description=f"Local directory: {path.name}",
            size_bytes=total_size,
            num_samples=num_samples,
            num_columns=num_columns,
            columns=columns,
            modality=DataModality.TABULAR,
            tasks=[],
            url=f"file://{path.absolute()}",
            raw_files=[str(f) for f in data_files],
        )

    def _find_data_files(self, path: Path) -> list[Path]:
        """Find all supported data files in directory."""
        files = []
        for ext in self.SUPPORTED_EXTENSIONS:
            files.extend(path.rglob(f"*{ext}"))
        return sorted(files)

    def _extract_schema(self, df: pl.DataFrame) -> list[ColumnInfo]:
        """Extract column schema from Polars DataFrame."""
        columns = []
        for col_name in df.columns:
            col_type = df[col_name].dtype
            nullable = df[col_name].null_count() > 0
            sample = df[col_name][0] if len(df) > 0 else None

            columns.append(
                ColumnInfo(
                    name=col_name,
                    dtype=str(col_type),
                    nullable=nullable,
                    description=f"Sample: {sample}" if sample is not None else None,
                )
            )
        return columns

    def _detect_format(self, path: Path) -> DataFormat:
        """Detect data format from file extension."""
        ext = path.suffix.lower()
        if ext == ".parquet":
            return DataFormat.PARQUET
        if ext == ".csv":
            return DataFormat.CSV
        if ext == ".jsonl":
            return DataFormat.JSONL
        if ext == ".json":
            return DataFormat.JSON
        if ext == ".arrow":
            return DataFormat.ARROW
        return DataFormat.UNKNOWN

    def _infer_modality(self, name: str, columns: list[ColumnInfo] | None = None) -> DataModality:
        """Infer modality from filename and columns."""
        name_lower = name.lower()

        if any(t in name_lower for t in ["image", "img", "picture", "photo"]):
            return DataModality.IMAGE
        if any(t in name_lower for t in ["audio", "sound", "speech", "voice"]):
            return DataModality.AUDIO
        if any(t in name_lower for t in ["text", "document", "article"]):
            return DataModality.TEXT

        # Check columns for image paths
        if columns:
            for col in columns:
                if col.dtype == "str" and ("image" in col.name.lower() or "path" in col.name.lower()):
                    return DataModality.IMAGE

        return DataModality.TABULAR

    async def download(
        self,
        path: str,
        output_dir: Path,
        *,
        revision: str | None = None,
        subset: str | None = None,
    ) -> AsyncIterator[DownloadProgress]:
        """Copy local file(s) to output directory.

        Args:
            path: Source path (file, directory, or glob pattern)
            output_dir: Output directory
            revision: Ignored for local files
            subset: Ignored for local files

        Yields:
            Download progress updates
        """
        import shutil
        import glob as glob_module

        source_path = Path(path)
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Handle glob patterns
        if "*" in str(path):
            files = glob_module.glob(path)
            if not files:
                raise ValueError(f"No files found matching pattern: {path}")

            for i, file_path in enumerate(sorted(files)):
                src = Path(file_path)
                dest = output_dir / src.name
                shutil.copy2(src, dest)

                yield DownloadProgress(
                    dataset_id=path,
                    source=DatasetSource.LOCAL,
                    current_bytes=i + 1,
                    total_bytes=len(files),
                    status="downloading",
                    file_name=src.name,
                )
            yield DownloadProgress(
                dataset_id=path,
                source=DatasetSource.LOCAL,
                current_bytes=len(files),
                total_bytes=len(files),
                status="completed",
            )
            return

        # Handle single file or directory
        if not source_path.exists():
            raise ValueError(f"Local path not found: {path}")

        if source_path.is_file():
            shutil.copy2(source_path, output_dir / source_path.name)
            yield DownloadProgress(
                dataset_id=path,
                source=DatasetSource.LOCAL,
                current_bytes=1,
                total_bytes=1,
                status="completed",
                file_name=source_path.name,
            )
        else:
            # Copy directory
            files = list(source_path.rglob("*"))
            data_files = [f for f in files if f.is_file() and f.suffix in self.SUPPORTED_EXTENSIONS]

            for i, src in enumerate(data_files):
                rel_path = src.relative_to(source_path)
                dest = output_dir / rel_path
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dest)

                yield DownloadProgress(
                    dataset_id=path,
                    source=DatasetSource.LOCAL,
                    current_bytes=i + 1,
                    total_bytes=len(data_files),
                    status="downloading",
                    file_name=str(rel_path),
                )

            yield DownloadProgress(
                dataset_id=path,
                source=DatasetSource.LOCAL,
                current_bytes=len(data_files),
                total_bytes=len(data_files),
                status="completed",
            )
