# mldata-cli v0.2.0 Technical Design

## Overview
This document describes the technical architecture for v0.2.0 features.

---

## 1. Local File Support

### Architecture Changes

#### New LocalConnector
```python
class LocalConnector(BaseConnector):
    """Connector for local files and directories."""

    name = "local"
    uri_schemes = ["file://", "./", "/", None]

    def __init__(self, path: Path | None = None):
        """Initialize with a path."""
        self.base_path = path.resolve() if path else Path.cwd()

    async def search(self, query: str = "", *, limit: int = 20, ...) -> list[SearchResult]:
        """Search local files matching query."""
        # Find all files matching extensions
        # Return SearchResult for each file

    async def get_metadata(self, path: str) -> DatasetMetadata:
        """Get metadata for a local file."""
        # Read file with Polars
        # Extract schema
        # Return metadata

    async def download(self, path: str, output_dir: Path, ...) -> AsyncIterator[DownloadProgress]:
        """Copy/link local file to output."""
        # Just copy the file
        yield DownloadProgress(...)
```

#### URI Format for Local Files
| Input | Parsed As |
|-------|-----------|
| `./data.csv` | Local file |
| `/absolute/path/data.csv` | Local file |
| `file:///path/data.csv` | Local file |
| `data/` | Local directory |
| `data/*.csv` | Glob pattern |

#### Path Detection Logic
```python
def detect_path_type(uri: str) -> tuple[str, dict]:
    """Detect if URI is local path."""
    if uri.startswith("file://"):
        path = uri[7:]
        return path, {"scheme": "file"}
    elif uri.startswith("./") or uri.startswith("../"):
        return uri, {"scheme": "local"}
    elif Path(uri).exists():
        return uri, {"scheme": "local"}
    elif uri.startswith("/") and Path(uri).exists():
        return uri, {"scheme": "local"}
    else:
        raise ValueError(f"Local path not found: {uri}")
```

---

## 2. Enhanced Info Command

#### Schema Extraction
```python
def extract_schema(df: pl.DataFrame) -> list[ColumnInfo]:
    """Extract schema from Polars DataFrame."""
    columns = []
    for col_name in df.columns:
        col_type = df[col_name].dtype
        nullable = df[col_name].null_count() > 0
        sample = df[col_name][0] if len(df) > 0 else None

        columns.append(ColumnInfo(
            name=col_name,
            dtype=str(col_type),
            nullable=nullable,
            description=f"Sample: {sample}"
        ))
    return columns
```

#### Updated DatasetMetadata
```python
class DatasetMetadata(BaseModel):
    # ... existing fields ...
    columns: list[ColumnInfo] | None = None  # NEW
    sample_rows: list[dict] | None = None     # NEW
    download_count: int | None = None         # EXISTING but not populated
    citation: str | None = None               # NEW
```

#### Info Output Format
```
╭────────────────── Dataset: titanic ───────────────────╮
│ Name: titanic                                        │
│ Source: huggingface                                  │
│ ID: phihung/titanic                                  │
│ Size: 5.1 MB                                         │
│ Modality: text                                       │
│ Tasks: classification                                │
│ License: other                                       │
│ Author: phihung                                      │
│ Downloads: 1,234                                     │
│ Version: 9753139e0b9d454ab4fd22e884290260db5fc7b6    │
│ URL: https://huggingface.co/datasets/phihung/titanic │
├──────────────────────────────────────────────────────┤
│ Schema (12 columns)                                  │
│ ┌──────────┬─────────┬─────────┬─────────────────┐  │
│ │ Name     │ Type    │ Nullable │ Sample          │  │
│ ├──────────┼─────────┼─────────┼─────────────────┤  │
│ │ PassengerId│ Int64  │ No      │ 1               │  │
│ │ Survived │ Float64 │ No      │ 0.0             │  │
│ │ Pclass   │ Int64   │ No      │ 3               │  │
│ │ Name     │ Str     │ No      │ "Braund, Mr..." │  │
│ └──────────┴─────────┴─────────┴─────────────────┘  │
├──────────────────────────────────────────────────────┤
│ Sample Rows                                          │
│ ┌────────┬──────────┬───────┬───────────────────┐   │
│ │ PassId │ Survived │ Class │ Name              │   │
│ ├────────┼──────────┼───────┼───────────────────┤   │
│ │ 1      │ 0.0      │ 3     │ "Braund, Mr..."   │   │
│ │ 2      │ 1.0      │ 1     │ "Cox, Mr. William"│   │
│ │ 3      │ 1.0      │ 3     │ "Heikkinen, Ms..."│   │
│ └────────┴──────────┴───────┴───────────────────┘   │
╰──────────────────────────────────────────────────────╯
```

---

## 3. OpenML Connector Fix

#### Updated OpenML Search
```python
async def search(self, query: str, *, limit: int = 20, ...) -> list[SearchResult]:
    """Search OpenML with dataframe response."""
    # Use output_format='dataframe' for new API
    datasets = openml.datasets.list_datasets(
        offset=0,
        size=limit,
        output_format='dataframe',  # NEW
    )

    # Handle both dict and dataframe responses
    if isinstance(datasets, dict):
        # Fallback for old API
        for did, d in datasets.items():
            # Process...
    else:
        # New dataframe API
        for _, row in datasets.iterrows():
            # Process row as dict
            d = row.to_dict()
            # ...
```

---

## 4. Validation Improvements

#### Enhanced Validation Output
```python
def check_missing_values(self, df: pl.DataFrame, max_ratio: float = 0.05):
    """Check for missing values with detailed output."""
    results = []
    total_rows = len(df)

    for col_name in df.columns:
        missing_count = df[col_name].null_count()
        missing_ratio = missing_count / total_rows

        if missing_ratio > max_ratio:
            results.append({
                "column": col_name,
                "missing_count": missing_count,
                "missing_ratio": missing_ratio,
                "severity": "error" if missing_ratio > 0.1 else "warning",
                "suggestion": f"Consider imputation or removal of '{col_name}'"
            })

    return {
        "check_name": "missing_values",
        "passed": len(results) == 0,
        "total_missing": sum(r["missing_count"] for r in results),
        "issues": results,
        "message": self._format_message(results)
    }
```

#### Output Format
```
Validating: /tmp/titanic
  Running duplicates...
    ✓ duplicates: PASS (0 duplicates found)
  Running missing...
    ✗ missing: FAIL (864 missing values across 4 columns)
    Columns with issues:
    - Age: 177 missing (19.9%) [ERROR] → Suggestion: Impute with median
    - Cabin: 687 missing (77.1%) [ERROR] → Suggestion: Remove column or impute
    - Embarked: 2 missing (0.2%) [WARNING] → Suggestion: Impute with mode
  Running schema...
    ✓ schema: PASS (12 columns, all types consistent)
```

---

## 5. Diff Command Enhancement

#### Data Comparison
```python
def compare_data(path1: Path, path2: Path) -> dict:
    """Compare two dataset builds."""
    # Load both datasets
    df1 = read_data(path1)
    df2 = read_data(path2)

    comparison = {
        "shape": {
            "path1": {"rows": len(df1), "columns": len(df1.columns)},
            "path2": {"rows": len(df2), "columns": len(df2.columns)},
            "match": len(df1) == len(df2) and len(df1.columns) == len(df2.columns)
        },
        "schema": compare_schema(df1, df2),
        "checksums": {
            "path1": compute_hash(read_all_bytes(path1)),
            "path2": compute_hash(read_all_bytes(path2)),
            "match": False
        },
        "sample_values": compare_sample(df1.head(5), df2.head(5))
    }

    return comparison
```

#### Output Format
```
Comparing: /tmp/build1 vs /tmp/build2
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Shape Comparison
  Rows:     891 vs 891  ✓ MATCH
  Columns:  12 vs 12    ✓ MATCH

Schema Comparison
  All 12 columns have matching types  ✓ MATCH

Checksums
  Data:     abc123... vs def456...  ✗ DIFFERENT
  This is expected if using different seeds!

Sample Values (first 5 rows)
  PassengerId: [1, 2, 3, 4, 5] vs [1, 2, 3, 4, 5]  ✓ MATCH
  Survived:    [0.0, 1.0, 1.0, 0.0, 0.0] vs [0.0, 1.0, 0.0, 1.0, 0.0]  ✗ DIFFERENT
  (Expected due to different split seeds)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Summary: Shapes match, data differs (expected with different seeds)
```

---

## 6. Rebuild Execution

#### Rebuild Flow
```python
async def rebuild(manifest_path: Path, output_dir: Path, **overrides):
    """Rebuild dataset from manifest."""
    # Load manifest
    manifest = load_manifest(manifest_path)

    # Extract parameters
    params = {
        "uri": manifest.source["uri"],
        "format": manifest.build.get("format", "parquet"),
        "split": manifest.build.get("split_ratios", [0.8, 0.1, 0.1]),
        "seed": manifest.build.get("seed"),
        "stratify": manifest.build.get("stratify"),
        **overrides  # Allow overrides
    }

    # Execute build
    await build_pipeline(**params)

    # Verify
    verification = verify_against_manifest(output_dir, manifest)

    return {"output_dir": output_dir, "verification": verification}
```

---

## 7. File Structure Changes

```
src/mldata/
├── connectors/
│   ├── local.py           # NEW: Local file connector
│   ├── huggingface.py     # Updated: Better metadata
│   ├── kaggle.py          # Minor updates
│   └── openml.py          # Updated: Fix dataframe API
├── models/
│   ├── dataset.py         # Updated: Add schema field
│   └── manifest.py        # Minor updates
├── core/
│   ├── fetch.py           # Updated: Local path handling
│   ├── validate.py        # Updated: Detailed output
│   └── diff.py            # NEW: Data comparison
└── cli/
    └── main.py            # Updated: All commands

tests/
├── unit/
│   ├── test_local_connector.py  # NEW
│   ├── test_validate.py         # UPDATED
│   └── test_diff.py             # NEW
└── integration/
    └── test_local_files.py      # NEW
```

---

## 8. Testing Strategy

### Unit Tests
- Test local path detection
- Test schema extraction
- Test validation logic
- Test diff comparison

### Integration Tests
- Test local file workflow end-to-end
- Test rebuild verification
- Test OpenML with mocked responses

### E2E Tests
- Full workflow: search → info → build → validate → diff

### Test Coverage Target: 85%
