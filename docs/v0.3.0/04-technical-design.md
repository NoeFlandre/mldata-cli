# mldata-cli v0.3.0 Technical Design

## Overview
This document describes the technical architecture for v0.3.0 features.

---

## 1. Parallel Processing

### Architecture

```
build pipeline:
  fetch -> normalize -> split -> validate -> export

parallel pipeline:
  - Split data into chunks
  - Process chunks concurrently using ThreadPoolExecutor
  - Merge results preserving order
```

#### ParallelNormalizeService
```python
class ParallelNormalizeService:
    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self.normalize = NormalizeService()

    async def convert_files_parallel(
        self,
        input_files: list[Path],
        output_dir: Path,
        format: str,
    ) -> list[Path]:
        """Convert multiple files in parallel."""
        import asyncio
        from concurrent.futures import ThreadPoolExecutor

        output_dir.mkdir(parents=True, exist_ok=True)

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            loop = asyncio.get_event_loop()
            tasks = [
                loop.run_in_executor(
                    executor,
                    self.normalize.convert_format,
                    input_file,
                    output_dir / f"{input_file.stem}.{format}",
                    format,
                )
                for input_file in input_files
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)

        return [r for r in results if not isinstance(r, Exception)]
```

#### Chunk-based Parallelism
```python
def split_into_chunks(df: pl.DataFrame, num_chunks: int) -> list[pl.DataFrame]:
    """Split DataFrame into chunks for parallel processing."""
    chunk_size = len(df) // num_chunks
    chunks = []
    for i in range(num_chunks):
        start = i * chunk_size
        end = start + chunk_size if i < num_chunks - 1 else len(df)
        chunks.append(df[start:end])
    return chunks

async def process_chunks_parallel(
    chunks: list[pl.DataFrame],
    process_fn: Callable,
    max_workers: int = 4,
) -> list[Any]:
    """Process chunks in parallel and return results."""
    import asyncio
    from concurrent.futures import ThreadPoolExecutor

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        loop = asyncio.get_event_loop()
        tasks = [
            loop.run_in_executor(executor, process_fn, chunk)
            for chunk in chunks
        ]
        return await asyncio.gather(*tasks)
```

---

## 2. Incremental Builds

#### Change Detection
```python
class IncrementalBuildService:
    def __init__(self, cache_dir: Path):
        self.cache_dir = cache_dir
        self.cache_file = cache_dir / "build_cache.json"

    def compute_file_hash(self, path: Path) -> str:
        """Compute SHA-256 hash of file."""
        import hashlib
        sha256 = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    def get_file_hashes(self, paths: list[Path]) -> dict[str, str]:
        """Get hash for each file."""
        return {str(p): self.compute_file_hash(p) for p in paths}

    def should_process(self, path: Path, previous_hash: str) -> bool:
        """Check if file should be processed."""
        current_hash = self.compute_file_hash(path)
        return current_hash != previous_hash

    def load_cache(self) -> dict:
        """Load build cache."""
        if self.cache_file.exists():
            import json
            return json.loads(self.cache_file.read_text())
        return {}

    def save_cache(self, cache: dict) -> None:
        """Save build cache."""
        import json
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_file.write_text(json.dumps(cache, indent=2))
```

#### Incremental Build Flow
```python
async def incremental_build(
    source_uri: str,
    output_dir: Path,
    previous_manifest: Manifest | None = None,
) -> BuildResult:
    """Run build with incremental processing."""
    # Get current file list
    current_files = get_source_files(source_uri)
    current_hashes = incremental_service.get_file_hashes(current_files)

    # Compare with previous build
    if previous_manifest:
        previous_hashes = previous_manifest.provenance.get("source_hashes", {})
        files_to_process = [
            f for f in current_files
            if incremental_service.should_process(f, previous_hashes.get(str(f)))
        ]
        files_to_skip = [
            f for f in current_files
            if not incremental_service.should_process(f, previous_hashes.get(str(f)))
        ]
    else:
        files_to_process = current_files
        files_to_skip = []

    console.print(f"Files to process: {len(files_to_process)}")
    console.print(f"Files skipped: {len(files_to_skip)}")

    # Process only changed files
    # ... processing logic ...

    # Update cache
    incremental_service.save_cache(current_hashes)
```

---

## 3. Data Profiling

#### Profile Service
```python
class ProfileService:
    """Service for dataset profiling and statistics."""

    def profile_dataset(self, path: Path) -> DatasetProfile:
        """Generate full profile of dataset."""
        df = self._read_data(path)

        profile = DatasetProfile(
            path=str(path),
            num_rows=len(df),
            num_columns=len(df.columns),
            file_size=path.stat().st_size if path.exists() else None,
            schema=self._profile_schema(df),
            statistics=self._compute_statistics(df),
            distributions=self._compute_distributions(df),
        )

        return profile

    def _profile_schema(self, df: pl.DataFrame) -> SchemaProfile:
        """Profile schema information."""
        return SchemaProfile(
            columns=[
                ColumnProfile(
                    name=col,
                    dtype=str(df[col].dtype),
                    nullable=df[col].null_count() > 0,
                    unique_count=df[col].n_unique(),
                )
                for col in df.columns
            ]
        )

    def _compute_statistics(self, df: pl.DataFrame) -> dict:
        """Compute statistical summary."""
        stats = {}
        numeric_cols = [c for c in df.columns if df[c].dtype in NUMERIC_DTYPES]

        for col in numeric_cols:
            col_data = df[col].drop_nulls()
            if len(col_data) > 0:
                stats[col] = {
                    "mean": float(col_data.mean()),
                    "std": float(col_data.std()) if len(col_data) > 1 else 0,
                    "min": float(col_data.min()),
                    "max": float(col_data.max()),
                    "percentiles": {
                        "25": float(col_data.quantile(0.25)),
                        "50": float(col_data.quantile(0.50)),
                        "75": float(col_data.quantile(0.75)),
                    },
                }

        return stats

    def _compute_distributions(self, df: pl.DataFrame) -> dict:
        """Compute value distributions for categorical columns."""
        dists = {}
        cat_cols = [c for c in df.columns if df[c].dtype == pl.Utf8]

        for col in cat_cols:
            value_counts = df[col].value_counts().head(20)
            dists[col] = {
                row["column"]: row["count"]
                for row in value_counts.to_dicts()
            }

        return dists


class DatasetProfile(BaseModel):
    """Full profile of a dataset."""
    path: str
    num_rows: int
    num_columns: int
    file_size: int | None = None
    schema: SchemaProfile
    statistics: dict = Field(default_factory=dict)
    distributions: dict = Field(default_factory=dict)

    def to_json(self, path: str) -> None:
        """Export profile to JSON."""
        import json
        with open(path, "w") as f:
            f.write(self.model_dump_json(indent=2))
```

---

## 4. Data Drift Detection

#### Drift Service
```python
class DriftService:
    """Service for detecting data drift between datasets."""

    def compute_psi(
        self,
        baseline: list[float],
        current: list[float],
        bins: int = 10,
    ) -> float:
        """Compute Population Stability Index (PSI).

        PSI = sum((actual% - expected%) * ln(actual% / expected%))
        """
        # Create bins
        baseline_bins = pd.cut(baseline, bins=bins, duplicates="drop")
        current_bins = pd.cut(current, bins=bins, duplicates="drop")

        # Calculate bin percentages
        baseline_pct = baseline_bins.value_counts(normalize=True).sort_index()
        current_pct = current_bins.value_counts(normalize=True).sort_index()

        # Align bins
        all_bins = baseline_pct.index.union(current_pct.index)
        baseline_pct = baseline_pct.reindex(all_bins, fill_value=0.001)  # Avoid log(0)
        current_pct = current_pct.reindex(all_bins, fill_value=0.001)

        # Calculate PSI
        psi = sum((current_pct - baseline_pct) * np.log(current_pct / baseline_pct))

        return float(psi)

    def compute_kl_divergence(
        self,
        p: list[float],
        q: list[float],
    ) -> float:
        """Compute KL Divergence D(P || Q).

        KL = sum(P[i] * log(P[i] / Q[i]))
        """
        p = np.array(p)
        q = np.array(q)

        # Normalize
        p = p / p.sum() if p.sum() > 0 else p
        q = q / q.sum() if q.sum() > 0 else q

        # Avoid log(0)
        p = np.clip(p, 1e-10, 1)
        q = np.clip(q, 1e-10, 1)

        return float(np.sum(p * np.log(p / q)))

    def detect_drift(
        self,
        baseline_df: pl.DataFrame,
        current_df: pl.DataFrame,
    ) -> DriftReport:
        """Detect drift between two datasets."""
        report = DriftReport()

        for col in baseline_df.columns:
            if baseline_df[col].dtype in NUMERIC_DTYPES:
                baseline_vals = baseline_df[col].drop_nulls().to_list()
                current_vals = current_df[col].drop_nulls().to_list()

                if len(baseline_vals) > 0 and len(current_vals) > 0:
                    psi = self.compute_psi(baseline_vals, current_vals)
                    drift_detected = psi > 0.1  # Common threshold

                    report.numeric_drift[col] = {
                        "psi": psi,
                        "drift_detected": drift_detected,
                        "severity": self._psi_to_severity(psi),
                    }

        return report

    def _psi_to_severity(self, psi: float) -> str:
        """Map PSI value to severity."""
        if psi < 0.05:
            return "low"
        elif psi < 0.1:
            return "medium"
        else:
            return "high"


class DriftReport(BaseModel):
    """Report of drift between datasets."""
    timestamp: datetime = Field(default_factory=datetime.now)
    numeric_drift: dict[str, dict] = Field(default_factory=dict)
    categorical_drift: dict[str, dict] = Field(default_factory=dict)

    @property
    def has_drift(self) -> bool:
        """Check if any drift detected."""
        return any(
            d.get("drift_detected", False)
            for d in {**self.numeric_drift, **self.categorical_drift}.values()
        )
```

---

## 5. Schema Evolution

#### Schema Versioning
```python
class SchemaEvolutionService:
    """Track schema changes across builds."""

    def compare_schemas(
        self,
        old_schema: list[ColumnInfo],
        new_schema: list[ColumnInfo],
    ) -> SchemaEvolution:
        """Compare two schemas and identify changes."""
        old_cols = {c.name: c for c in old_schema}
        new_cols = {c.name: c for c in new_schema}

        added = [new_cols[n] for n in new_cols if n not in old_cols]
        removed = [old_cols[n] for n in old_cols if n not in new_cols]
        changed = []

        for name in set(old_cols.keys()) & set(new_cols.keys()):
            if old_cols[name].dtype != new_cols[name].dtype:
                changed.append({
                    "column": name,
                    "old_type": old_cols[name].dtype,
                    "new_type": new_cols[name].dtype,
                })

        return SchemaEvolution(
            added_columns=added,
            removed_columns=removed,
            type_changes=changed,
            breaking_changes=[c for c in changed if self._is_breaking_change(c)],
        )

    def _is_breaking_change(self, change: dict) -> bool:
        """Check if a type change is breaking."""
        # Example: int -> str is breaking, str -> int might be
        return True  # Conservative approach


class SchemaEvolution(BaseModel):
    """Schema evolution report."""
    added_columns: list[ColumnInfo] = Field(default_factory=list)
    removed_columns: list[ColumnInfo] = Field(default_factory=list)
    type_changes: list[dict] = Field(default_factory=list)
    breaking_changes: list[dict] = Field(default_factory=list)
```

---

## 6. Compression Options

#### Export Service Updates
```python
class ExportService:
    COMPRESSION_MAP = {
        "snappy": {"parquet": "snappy"},
        "gzip": {"parquet": "gzip", "csv": "gzip"},
        "zstd": {"parquet": "zstd"},
        "none": {"parquet": None},
    }

    def export(
        self,
        df: pl.DataFrame,
        output_path: Path,
        format: str,
        compression: str | None = None,
    ) -> None:
        """Export with specified compression."""
        compression_map = self.COMPRESSION_MAP.get(compression or "snappy", {})
        fmt_compression = compression_map.get(format)

        if format == "parquet":
            df.write_parquet(
                output_path,
                compression=fmt_compression,
            )
        elif format == "csv":
            if fmt_compression:
                import gzip
                with gzip.open(output_path, "wt") as f:
                    df.write_csv(f)
            else:
                df.write_csv(output_path)
        # ... other formats
```

---

## 7. File Structure Changes

```
src/mldata/
├── core/
│   ├── profile.py        # NEW: Profiling service
│   ├── drift.py          # NEW: Drift detection service
│   ├── parallel.py       # NEW: Parallel processing
│   ├── incremental.py    # NEW: Incremental builds
│   └── ...
├── cli/
│   └── main.py           # Updated: profile command
└── models/
    ├── profile.py        # NEW: Profile models
    └── drift.py          # NEW: Drift models

tests/
├── unit/
│   ├── test_profile.py   # NEW
│   ├── test_drift.py     # NEW
│   └── test_parallel.py  # NEW
└── integration/
    └── test_profile.py   # NEW
```

---

## 8. Testing Strategy

### Unit Tests
- Test PSI calculation with known values
- Test KL divergence with known distributions
- Test parallel processing with mocked I/O
- Test incremental build change detection

### Integration Tests
- Test full profile workflow
- Test drift detection between real datasets
- Test compression output sizes

### E2E Tests
- Profile command end-to-end
- Build with incremental flag

### Test Coverage Target: 85%
