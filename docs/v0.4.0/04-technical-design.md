# mldata-cli v0.4.0 Technical Design

## Document Control

| Field | Value |
|-------|-------|
| **Version** | 0.4.0 |
| **Date** | 2026-01-29 |
| **Author** | Noé Flandre |
| **Status** | Draft |
| **Parent Document** | [03-sprint-backlog.md](./03-sprint-backlog.md) |

---

## Architecture Overview

v0.4.0 adds download reliability, file integrity validation, and external integration features to the existing architecture.

```
mldata-cli/
├── src/mldata/
│   ├── cli/
│   │   └── main.py          # Updated: --dvc, --git-lfs, --formats flags
│   ├── core/
│   │   ├── fetch.py         # Updated: resume support
│   │   ├── validate.py      # Updated: file integrity checks
│   │   └── export.py        # Updated: multi-format, framework templates
│   ├── connectors/
│   │   └── base.py          # Updated: range request support
│   ├── integrations/        # NEW: DVC, Git-LFS integration
│   │   ├── __init__.py
│   │   ├── dvc.py
│   │   └── gitlfs.py
│   └── utils/
│       └── progress.py      # Updated: enhanced ETA
```

---

## Feature: Download Resume (US-036)

### Data Structures

```python
class PartialDownload:
    """State for interrupted downloads."""
    path: Path
    temp_path: Path
    url: str
    expected_size: int
    downloaded_size: int
    etag: str | None
    last_modified: str | None
    created_at: datetime
```

### Flow

```
1. User runs: mldata pull hf://dataset
2. Check for partial download in cache
3. If found:
   - Verify source hasn't changed (ETag)
   - Resume download from downloaded_size
4. If not found:
   - Start fresh download
5. On completion:
   - Move temp to final location
   - Clean up partial files
```

### Range Request Support

```python
async def fetch_with_resume(
    url: str,
    output_path: Path,
    resume_from: int = 0
) -> None:
    """Fetch with range request for resume support."""
    headers = {"Range": f"bytes={resume_from}-"}
    async with httpx.AsyncClient() as client:
        async with client.stream("GET", url, headers=headers) as response:
            # Handle 206 Partial Content or 200 OK
            ...
```

---

## Feature: File Integrity Checks (US-037)

### Validation Flow

```
validate --checks files
    ↓
1. Detect file type (image, audio, tabular)
2. For images:
   - Try to open with PIL.Image.open()
   - Check for truncation
   - Verify dimensions
3. For audio:
   - Try to read with audiofile
   - Check duration matches file size
4. Report results
```

### Data Model

```python
class FileCheckResult(BaseModel):
    """Result of file integrity check."""
    path: Path
    file_type: str  # "image", "audio", "tabular"
    is_valid: bool
    error: str | None = None
    details: dict = {}
```

### Supported Formats

| Type | Extensions | Validation |
|------|------------|------------|
| Images | .jpg, .jpeg, .png, .gif, .bmp | PIL open, dimensions |
| Audio | .wav, .mp3, .flac, .ogg | audiofile duration |
| Video | .mp4, .avi (future) | - |

---

## Feature: DVC Integration (US-038)

### DVC File Format

```yaml
# data.dvc
outs:
- md5: abc123...
  path: data/
  cache: true
  remote: myremote
```

### Integration Flow

```
mldata export --dvc ./dataset
    ↓
1. Generate .dvc file with manifest hashes
2. Verify .dvc syntax
3. Update .dvcignore if needed
4. Show git commands to run
```

### Implementation

```python
class DVCService:
    """Service for DVC integration."""

    def generate_dvc_file(
        self,
        dataset_path: Path,
        manifest: Manifest
    ) -> Path:
        """Generate .dvc file for dataset."""
        dvc_content = {
            "outs": [{
                "path": dataset_path.name,
                "cache": True,
                "md5": manifest.provenance.source_hash,
            }]
        }
        dvc_path = dataset_path.parent / f"{dataset_path.name}.dvc"
        dvc_path.write_text(yaml.dump(dvc_content))
        return dvc_path
```

---

## Feature: Git-LFS Integration (US-039)

### Pattern Selection

| Pattern | File Types |
|---------|------------|
| `*.parquet` | Parquet datasets |
| `*.csv` | CSV files >10MB |
| `*.jsonl` | JSON Lines >10MB |
| `*.zip` | Archived datasets |

### Integration Flow

```
mldata export --git-lfs ./dataset
    ↓
1. Check if .gitattributes exists
2. Detect large files in dataset
3. Generate patterns for large files
4. Append patterns to .gitattributes
5. Show git commands
```

---

## Feature: Multi-Format Export (US-040)

### Implementation

```python
class ExportService:
    async def export_multiple_formats(
        self,
        df: pl.DataFrame,
        output_dir: Path,
        formats: list[str],
        compression: str | None = None
    ) -> dict[str, Path]:
        """Export to multiple formats in single pass."""
        # Read data once
        data = df

        outputs = {}
        for fmt in formats:
            path = output_dir / f"data.{fmt}"
            outputs[fmt] = self.export(data, path, format=fmt, compression=compression)

        return outputs
```

---

## Feature: Framework Templates (US-041)

### PyTorch Structure

```
dataset/
├── manifest.yaml
├── train.csv          # Split data
├── val.csv
├── test.csv
├── images/            # Raw files (if applicable)
└── README.md          # Generated with loader code
```

### Generated Loader Code

```python
# dataset/dataset.py (generated)
from torch.utils.data import Dataset
import pandas as pd
from PIL import Image
from pathlib import Path

class MyDataset(Dataset):
    def __init__(self, csv_path, root_dir, transform=None):
        self.annotations = pd.read_csv(csv_path)
        self.root_dir = Path(root_dir)
        self.transform = transform

    def __len__(self):
        return len(self.annotations)

    def __getitem__(self, idx):
        # Implementation generated based on schema
        ...
```

---

## Dependencies

### New Dependencies

```toml
# pyproject.toml additions
PIL = { version = ">=10.0", optional = true }  # Image validation
audiofile = { version = ">=0.1", optional = true }  # Audio validation
mutagen = { version = ">=1.47", optional = true }  # Audio metadata
```

### Existing Dependencies Updated

- `httpx`: Required for range request support
- `pyyaml`: Required for DVC file generation

---

## Testing Strategy

### Unit Tests

| Feature | Tests |
|---------|-------|
| Download Resume | `test_resume_*` (5 tests) |
| File Integrity | `test_files_*` (8 tests) |
| DVC Integration | `test_dvc_*` (4 tests) |
| Git-LFS | `test_lfs_*` (3 tests) |
| Multi-Format | `test_multi_format_*` (4 tests) |
| Framework Export | `test_framework_*` (3 tests) |

### Integration Tests

- Mock DVC API responses with VCR.py
- Test .gitattributes updates
- Validate .dvc file syntax

---

## Performance Considerations

1. **File Validation**: Use sampling for very large datasets
2. **Multi-Format Export**: Single data read, multiple writes
3. **DVC Integration**: SHA-256 reuse from manifest

---

## Security Considerations

1. **DVC Files**: Validate paths to prevent directory traversal
2. **Git-LFS**: Don't overwrite existing patterns
3. **Resume**: Clean up temp files on failure

---

**End of Document**
