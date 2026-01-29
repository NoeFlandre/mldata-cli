"""Parallel processing service for concurrent dataset operations."""

from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, TypeVar

import polars as pl

T = TypeVar("T")


class ParallelService:
    """Service for parallel processing of datasets."""

    def __init__(self, max_workers: int | None = None):
        """Initialize parallel service.

        Args:
            max_workers: Maximum concurrent workers. Defaults to CPU count.
        """
        import os

        self.max_workers = max_workers or os.cpu_count() or 4

    def process_files_parallel(
        self,
        files: list[Path],
        process_fn: Callable[[Path], tuple[Path, Any]],
        output_dir: Path | None = None,
        desc: str = "Processing",
    ) -> list[tuple[Path, Any]]:
        """Process multiple files in parallel.

        Args:
            files: List of files to process
            process_fn: Function to apply to each file, returns (output_path, result)
            output_dir: Output directory (created if needed)
            desc: Description for progress

        Returns:
            List of (output_path, result) tuples
        """
        if output_dir:
            output_dir.mkdir(parents=True, exist_ok=True)

        results: list[tuple[Path, Any]] = []

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {executor.submit(process_fn, f): f for f in files}

            for future in as_completed(futures):
                try:
                    output_path, result = future.result()
                    results.append((output_path, result))
                except Exception as e:
                    file_path = futures[future]
                    results.append((file_path, Exception(str(e))))

        return results

    def convert_files_parallel(
        self,
        input_files: list[Path],
        output_dir: Path,
        target_format: str,
        compression: str | None = None,
    ) -> list[tuple[Path, bool]]:
        """Convert multiple files to target format in parallel.

        Args:
            input_files: List of input files
            output_dir: Output directory
            target_format: Target format (csv, json, jsonl, parquet)
            compression: Compression type for parquet

        Returns:
            List of (output_path, success) tuples
        """
        from mldata.core.normalize import NormalizeService

        normalize = NormalizeService()

        def convert_one(input_file: Path) -> tuple[Path, bool]:
            output_path = output_dir / f"{input_file.stem}.{target_format}"
            try:
                normalize.convert_format(input_file, output_path, target_format, compression)
                return (output_path, True)
            except Exception:
                return (output_path, False)

        results = self.process_files_parallel(input_files, convert_one, output_dir, "Converting")
        return [(p, not isinstance(r, Exception)) for p, r in results]

    def split_dataframe_parallel(
        self,
        df: "pl.DataFrame",
        num_chunks: int,
        split_fn: Callable[["pl.DataFrame"], dict[str, "pl.DataFrame"]],
    ) -> list[dict[str, "pl.DataFrame"]]:
        """Split DataFrame and process chunks in parallel.

        Args:
            df: DataFrame to split
            num_chunks: Number of chunks to split into
            split_fn: Function to apply to each chunk

        Returns:
            List of result dicts from each chunk
        """
        # Split into chunks
        chunk_size = len(df) // num_chunks
        chunks = []
        for i in range(num_chunks):
            start = i * chunk_size
            end = start + chunk_size if i < num_chunks - 1 else len(df)
            chunks.append(df[start:end])

        # Process chunks in parallel
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {executor.submit(split_fn, chunk): i for i, chunk in enumerate(chunks)}
            results: list[dict[str, pl.DataFrame]] = [{}] * len(chunks)

            for future in as_completed(futures):
                idx = futures[future]
                results[idx] = future.result()

        return results

    def merge_results(
        self,
        results: list[dict[str, Any]],
        key: str,
    ) -> list[Any]:
        """Merge results from parallel processing, preserving order.

        Args:
            results: List of result dicts containing order key
            key: Key for ordering value

        Returns:
            Merged list in original order
        """
        sorted_results = sorted(results, key=lambda x: x.get(key, 0))
        return [r.get("data") for r in sorted_results if "data" in r]
