"""Framework export templates service."""

from dataclasses import dataclass
from pathlib import Path

import polars as pl


@dataclass
class FrameworkExportResult:
    """Result of framework export operation."""

    success: bool
    output_dir: Path | None = None
    files_created: list[str] | None = None
    loader_code: str = ""
    error: str | None = None

    def __post_init__(self):
        if self.files_created is None:
            self.files_created = []


class FrameworkExportService:
    """Service for exporting datasets in framework-specific formats."""

    SUPPORTED_FRAMEWORKS = {"pytorch", "tensorflow", "jax"}

    def __init__(self):
        """Initialize framework export service."""
        pass

    def get_framework(self, framework: str) -> "FrameworkExporter":
        """Get exporter for a specific framework.

        Args:
            framework: Framework name

        Returns:
            FrameworkExporter instance
        """
        framework = framework.lower()

        if framework == "pytorch":
            return PyTorchExporter()
        elif framework in ("tensorflow", "tf"):
            return TensorFlowExporter()
        elif framework == "jax":
            return JAXExporter()
        else:
            raise ValueError(f"Unsupported framework: {framework}. Supported: {self.SUPPORTED_FRAMEWORKS}")


class FrameworkExporter:
    """Base class for framework-specific exporters."""

    framework_name: str = "base"

    def export(
        self,
        df: pl.DataFrame,
        output_dir: Path,
        dataset_name: str = "dataset",
        schema: dict | None = None,
    ) -> FrameworkExportResult:
        """Export dataset in framework-specific format.

        Args:
            df: Polars DataFrame
            output_dir: Output directory
            dataset_name: Name of the dataset
            schema: Dataset schema info

        Returns:
            FrameworkExportResult with export status
        """
        raise NotImplementedError

    def generate_loader_code(
        self,
        dataset_name: str,
        columns: list[str],
        column_types: dict[str, str],
        split: str | None = None,
    ) -> str:
        """Generate loader code for the dataset.

        Args:
            dataset_name: Name of the dataset
            columns: Column names
            column_types: Column type mapping
            split: Optional split name

        Returns:
            String containing loader code
        """
        raise NotImplementedError

    def _write_readme(
        self,
        output_dir: Path,
        dataset_name: str,
        columns: list[str],
        column_types: dict[str, str],
        loader_code: str,
    ) -> None:
        """Write README with loading instructions.

        Args:
            output_dir: Output directory
            dataset_name: Name of the dataset
            columns: Column names
            column_types: Column type mapping
            loader_code: Generated loader code
        """
        readme_content = f"""# {dataset_name}

Dataset exported from mldata-cli.

## Structure

```
{dataset_name}/
├── data/              # Data files
├── splits/            # Train/val/test splits (if applicable)
└── README.md          # This file
```

## Loading in {self.framework_name}

```python
{loader_code}
```

## Schema

| Column | Type |
|--------|------|
"""

        for col, dtype in column_types.items():
            readme_content += f"| {col} | {dtype} |\n"

        readme_path = output_dir / "README.md"
        readme_path.write_text(readme_content)


class PyTorchExporter(FrameworkExporter):
    """PyTorch-specific dataset exporter."""

    framework_name = "PyTorch"

    def export(
        self,
        df: pl.DataFrame,
        output_dir: Path,
        dataset_name: str = "dataset",
        schema: dict | None = None,
    ) -> FrameworkExportResult:
        """Export dataset in PyTorch format.

        Args:
            df: Polars DataFrame
            output_dir: Output directory
            dataset_name: Name of the dataset
            schema: Dataset schema info

        Returns:
            FrameworkExportResult with export status
        """
        try:
            # Create data directory
            data_dir = output_dir / "data"
            data_dir.mkdir(parents=True, exist_ok=True)

            # Export as Parquet (PyTorch can read with loaders)
            export = __import__("mldata.core.export", fromlist=["ExportService"]).ExportService()
            output_path = data_dir / "data.parquet"
            export.export(df, output_path, format="parquet")

            # Generate loader code
            columns = df.columns
            column_types = {col: str(df[col].dtype) for col in columns}
            loader_code = self.generate_loader_code(dataset_name, columns, column_types)

            # Write README with loader code
            self._write_readme(output_dir, dataset_name, columns, column_types, loader_code)

            return FrameworkExportResult(
                success=True,
                output_dir=output_dir,
                files_created=[str(data_dir / "data.parquet"), "README.md"],
                loader_code=loader_code,
            )

        except Exception as e:
            return FrameworkExportResult(
                success=False,
                error=str(e),
            )

    def generate_loader_code(
        self,
        dataset_name: str,
        columns: list[str],
        column_types: dict[str, str],
        split: str | None = None,
    ) -> str:
        """Generate PyTorch DataLoader code.

        Args:
            dataset_name: Name of the dataset
            columns: Column names
            column_types: Column type mapping
            split: Optional split name

        Returns:
            String containing PyTorch loader code
        """
        # Detect target column (look for common names)
        target_cols = ["label", "target", "class", "y"]
        target_col = next((c for c in columns if c.lower() in target_cols), None)

        # Format column names for the generated code
        feature_cols = [c for c in columns if c != target_col]
        feature_str = "{" + ", ".join(f'"{c}": row["{c}"]' for c in feature_cols) + "}"

        if target_col:
            target_code = f'''    def __getitem__(self, idx):
        row = self.data[idx]
        x = {feature_str}
        y = row["{target_col}"]
        return x, y
'''
        else:
            feature_str_all = "{" + ", ".join(f'"{c}": row["{c}"]' for c in columns) + "}"
            target_code = f"""    def __getitem__(self, idx):
        row = self.data[idx]
        x = {feature_str_all}
        return x
"""

        code = f'''import polars as pl
from torch.utils.data import Dataset, DataLoader

class {dataset_name.replace("-", "_").title().replace("_", "")}Dataset(Dataset):
    """{dataset_name} dataset for PyTorch."""

    def __init__(self, data_path: str, split: str = "train"):
        super().__init__()
        self.data = pl.read_parquet(f"{{data_path}}/{{split}}.parquet")

    def __len__(self):
        return len(self.data){target_code}

# Usage
train_dataset = {dataset_name.replace("-", "_").title().replace("_", "")}Dataset("./{dataset_name}/data", split="train")
train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True)

# Iterate
for batch_x, batch_y in train_loader:
    # Your training code here
    pass
'''
        return code


class TensorFlowExporter(FrameworkExporter):
    """TensorFlow-specific dataset exporter."""

    framework_name = "TensorFlow"

    def export(
        self,
        df: pl.DataFrame,
        output_dir: Path,
        dataset_name: str = "dataset",
        schema: dict | None = None,
    ) -> FrameworkExportResult:
        """Export dataset in TensorFlow format.

        Args:
            df: Polars DataFrame
            output_dir: Output directory
            dataset_name: Name of the dataset
            schema: Dataset schema info

        Returns:
            FrameworkExportResult with export status
        """
        try:
            # Create data directory
            data_dir = output_dir / "data"
            data_dir.mkdir(parents=True, exist_ok=True)

            # Export as Parquet (TF can read with loaders)
            export = __import__("mldata.core.export", fromlist=["ExportService"]).ExportService()
            output_path = data_dir / "data.parquet"
            export.export(df, output_path, format="parquet")

            # Generate loader code
            columns = df.columns
            column_types = {col: str(df[col].dtype) for col in columns}
            loader_code = self.generate_loader_code(dataset_name, columns, column_types)

            # Write README with loader code
            self._write_readme(output_dir, dataset_name, columns, column_types, loader_code)

            return FrameworkExportResult(
                success=True,
                output_dir=output_dir,
                files_created=[str(data_dir / "data.parquet"), "README.md"],
                loader_code=loader_code,
            )

        except Exception as e:
            return FrameworkExportResult(
                success=False,
                error=str(e),
            )

    def generate_loader_code(
        self,
        dataset_name: str,
        columns: list[str],
        column_types: dict[str, str],
        split: str | None = None,
    ) -> str:
        """Generate TensorFlow dataset code.

        Args:
            dataset_name: Name of the dataset
            columns: Column names
            column_types: Column type mapping
            split: Optional split name

        Returns:
            String containing TensorFlow loader code
        """
        # Detect target column
        target_cols = ["label", "target", "class", "y"]
        target_col = next((c for c in columns if c.lower() in target_cols), None)

        if target_col:
            code = f'''import tensorflow as tf
import polars as pl

def load_{dataset_name.replace("-", "_")}(data_path: str, split: str = "train"):
    """Load {dataset_name} dataset.

    Args:
        data_path: Path to data directory
        split: Dataset split ("train", "val", "test")

    Returns:
        tf.data.Dataset
    """
    df = pl.read_parquet(f"{{data_path}}/{{split}}.parquet")

    def convert_to_tensor(row):
        features = {{}}
        labels = {{}}
        for col, val in row.items():
            if col == "{target_col}":
                labels["label"] = tf.constant(val)
            else:
                features[col] = tf.constant(val)
        return features, labels

    ds = df.map_rows(convert_to_tensor)
    ds = ds.batch(32)
    ds = ds.prefetch(tf.data.AUTOTUNE)
    return ds

# Usage
train_ds = load_{dataset_name.replace("-", "_")}("./{dataset_name}/data", split="train")

for features, labels in train_ds:
    # Your training code here
    print("Features:", features)
    print("Labels:", labels)
'''
        else:
            code = '''import tensorflow as tf
import polars as pl

def load_dataset(data_path: str, split: str = "train"):
    """Load dataset."""
    df = pl.read_parquet(f"{data_path}/{split}.parquet")
    return tf.data.Dataset.from_tensor_slices(df.to_dict(as_series=False))

# Usage
train_ds = load_dataset("./data", split="train")
train_ds = train_ds.batch(32)
'''

        return code


class JAXExporter(FrameworkExporter):
    """JAX-specific dataset exporter."""

    framework_name = "JAX"

    def export(
        self,
        df: pl.DataFrame,
        output_dir: Path,
        dataset_name: str = "dataset",
        schema: dict | None = None,
    ) -> FrameworkExportResult:
        """Export dataset in JAX format.

        Args:
            df: Polars DataFrame
            output_dir: Output directory
            dataset_name: Name of the dataset
            schema: Dataset schema info

        Returns:
            FrameworkExportResult with export status
        """
        try:
            # Create data directory
            data_dir = output_dir / "data"
            data_dir.mkdir(parents=True, exist_ok=True)

            # Export as numpy .npz files (JAX works well with numpy)
            import numpy as np

            for split_name, split_df in [
                ("train", df.head(len(df) * 8 // 10)),
                ("val", df.tail(len(df) * 2 // 10)),
                ("test", df.tail(len(df) - len(df) * 8 // 10 - len(df) * 2 // 10)),
            ]:
                output_path = data_dir / f"{split_name}.npz"
                # Convert to numpy arrays and save
                arrays = {col: split_df[col].to_numpy() for col in split_df.columns}
                np.savez(output_path, **arrays)

            # Generate loader code
            columns = df.columns
            column_types = {col: str(df[col].dtype) for col in columns}
            loader_code = self.generate_loader_code(dataset_name, columns, column_types)

            # Write README
            self._write_readme(output_dir, dataset_name, columns, column_types, loader_code)

            return FrameworkExportResult(
                success=True,
                output_dir=output_dir,
                files_created=["data/train.npz", "data/val.npz", "data/test.npz", "README.md"],
                loader_code=loader_code,
            )

        except Exception as e:
            return FrameworkExportResult(
                success=False,
                error=str(e),
            )

    def generate_loader_code(
        self,
        dataset_name: str,
        columns: list[str],
        column_types: dict[str, str],
        split: str | None = None,
    ) -> str:
        """Generate JAX dataset code.

        Args:
            dataset_name: Name of the dataset
            columns: Column names
            column_types: Column type mapping
            split: Optional split name

        Returns:
            String containing JAX loader code
        """
        # Detect target column
        target_cols = ["label", "target", "class", "y"]
        target_col = next((c for c in columns if c.lower() in target_cols), None)

        if target_col:
            feature_cols = [c for c in columns if c != target_col]
            code = f'''import jax
import jax.numpy as jnp
import numpy as np

def load_{dataset_name.replace("-", "_")}(data_dir: str, split: str = "train"):
    """Load {dataset_name} dataset.

    Args:
        data_dir: Path to data directory
        split: Dataset split ("train", "val", "test")

    Returns:
        Tuple of (features, labels) as JAX arrays
    """
    data = np.load(f"{{data_dir}}/{{split}}.npz")
    features = jnp.array(data["{feature_cols[0]}"]) if len("{feature_cols}".split(",")) == 1 else \\
               jnp.stack([data[col] for col in {feature_cols}], axis=-1)
    labels = jnp.array(data["{target_col}"])
    return features, labels

# Usage
x_train, y_train = load_{dataset_name.replace("-", "_")}("./{dataset_name}/data", split="train")
print(f"X shape: {{x_train.shape}}, Y shape: {{y_train.shape}}")
'''
        else:
            code = '''import jax
import jax.numpy as jnp
import numpy as np

def load_dataset(data_dir: str, split: str = "train"):
    """Load dataset as JAX arrays."""
    data = np.load(f"{data_dir}/{split}.npz")
    return {col: jnp.array(data[col]) for col in data.keys()}

# Usage
data = load_dataset("./data", split="train")
'''

        return code


def export_dataset(
    df: pl.DataFrame,
    output_dir: Path,
    format: str = "parquet",
    framework: str | None = None,
    compression: str | None = None,
    dataset_name: str = "dataset",
) -> FrameworkExportResult:
    """Convenience function to export dataset.

    Args:
        df: Polars DataFrame
        output_dir: Output directory
        format: Export format
        framework: Framework to export for (optional)
        compression: Compression type
        dataset_name: Name of the dataset

    Returns:
        FrameworkExportResult
    """
    if framework:
        exporter = FrameworkExportService().get_framework(framework)
        return exporter.export(df, output_dir, dataset_name=dataset_name)
    else:
        export = __import__("mldata.core.export", fromlist=["ExportService"]).ExportService()
        output_path = output_dir / f"data.{format}"
        export.export(df, output_path, format=format, compression=compression)
        return FrameworkExportResult(
            success=True,
            output_dir=output_dir,
            files_created=[str(output_path)],
        )
