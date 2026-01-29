"""Split service for train/val/test splitting."""

import random
from pathlib import Path
from typing import Iterator

import polars as pl


class SplitService:
    """Service for splitting datasets."""

    def __init__(self):
        """Initialize split service."""
        pass

    def split(
        self,
        df: pl.DataFrame,
        ratios: list[float] | None = None,
        seed: int | None = None,
        stratify_column: str | None = None,
    ) -> dict[str, pl.DataFrame]:
        """Split DataFrame into train/val/test sets.

        Args:
            df: Polars DataFrame
            ratios: Split ratios [train, val, test]
            seed: Random seed for reproducibility
            stratify_column: Column to stratify on

        Returns:
            Dict with 'train', 'val', 'test' keys
        """
        if ratios is None:
            ratios = [0.8, 0.1, 0.1]

        if len(ratios) != 3:
            raise ValueError("Must provide exactly 3 ratios (train, val, test)")

        if abs(sum(ratios) - 1.0) > 0.001:
            raise ValueError("Ratios must sum to 1.0")

        # Create shuffled indices
        indices = list(range(len(df)))
        if seed is not None:
            random.seed(seed)

        random.shuffle(indices)

        # Calculate split points
        n = len(df)
        train_end = int(n * ratios[0])
        val_end = train_end + int(n * ratios[1])

        train_indices = indices[:train_end]
        val_indices = indices[train_end:val_end]
        test_indices = indices[val_end:]

        # Stratified split if needed
        if stratify_column and stratify_column in df.columns:
            train_indices, val_indices, test_indices = self._stratified_split(
                df, stratify_column, ratios, seed
            )

        return {
            "train": df[train_indices],
            "val": df[val_indices],
            "test": df[test_indices],
        }

    def _stratified_split(
        self,
        df: pl.DataFrame,
        stratify_column: str,
        ratios: list[float],
        seed: int | None = None,
    ) -> tuple[list[int], list[int], list[int]]:
        """Perform stratified split preserving label distribution.

        Args:
            df: Polars DataFrame
            stratify_column: Column to stratify on
            ratios: Split ratios
            seed: Random seed

        Returns:
            Tuple of (train_indices, val_indices, test_indices)
        """
        if seed is not None:
            random.seed(seed)

        train_indices = []
        val_indices = []
        test_indices = []

        # Get unique labels and their indices
        labels = df[stratify_column].to_list()
        unique_labels = list(set(labels))

        for label in unique_labels:
            # Get indices for this label
            label_indices = [i for i, l in enumerate(labels) if l == label]
            n = len(label_indices)
            train_end = int(n * ratios[0])
            val_end = train_end + int(n * ratios[1])

            random.shuffle(label_indices)

            train_indices.extend(label_indices[:train_end])
            val_indices.extend(label_indices[train_end:val_end])
            test_indices.extend(label_indices[val_end:])

        return train_indices, val_indices, test_indices

    def save_splits(
        self,
        splits: dict[str, pl.DataFrame],
        output_dir: Path,
        format: str = "csv",
    ) -> dict[str, Path]:
        """Save split DataFrames to files.

        Args:
            splits: Dict of split name to DataFrame
            output_dir: Output directory
            format: Output format (csv, parquet, jsonl)

        Returns:
            Dict mapping split name to output path
        """
        output_paths = {}

        # Ensure output directory exists
        output_dir.mkdir(parents=True, exist_ok=True)

        for split_name, df in splits.items():
            output_path = output_dir / f"{split_name}.{format}"
            output_paths[split_name] = output_path

            if format == "csv":
                df.write_csv(output_path)
            elif format == "parquet":
                df.write_parquet(output_path)
            elif format == "jsonl":
                df.write_ndjson(output_path)

        return output_paths

    def save_split_indices(
        self,
        splits: dict[str, pl.DataFrame],
        output_dir: Path,
        base_indices: list[int] | None = None,
    ) -> dict[str, Path]:
        """Save split assignments as index files.

        Args:
            splits: Dict of split name to DataFrame
            output_dir: Output directory
            base_indices: Base indices if using non-contiguous indexing

        Returns:
            Dict mapping split name to output path
        """
        output_paths = {}

        for split_name, df in splits.items():
            output_path = output_dir / f"{split_name}_indices.csv"
            output_paths[split_name] = output_path

            # Create index file with actual indices
            indices = list(range(len(df)))
            index_df = pl.DataFrame({"row_index": indices, "split": [split_name] * len(indices)})
            index_df.write_csv(output_path)

        return output_paths
