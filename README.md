# mldata-cli v0.4.0

<div align="center">

![mldata-cli Overview](assets/image.png)

**A unified, reproducible CLI for ML dataset acquisition and preparation**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://python.org)
[![MIT License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

</div>

---

## 🎧 Vibe Coding Disclaimer

**Disclaimer**
This repository **was vibe coded**.

---

## Table of Contents

1. [What is mldata-cli?](#what-is-mldata-cli)
2. [Why Use mldata-cli?](#why-use-mldata-cli)
3. [Installation](#installation)
4. [Quick Start](#quick-start)
5. [Core Concepts](#core-concepts)
6. [Commands Reference](#commands-reference)
7. [Data Sources](#data-sources)
8. [Output Formats](#output-formats)
9. [Advanced Features](#advanced-features)
10. [Configuration](#configuration)
11. [Contributing](#contributing)

---

## What is mldata-cli?

mldata-cli is a command-line tool that simplifies the entire machine learning dataset lifecycle:

- **Discover** datasets across HuggingFace, Kaggle, and OpenML
- **Download** with automatic resume on interruption
- **Process** normalize, validate, split, and transform data
- **Export** to multiple formats with framework-specific loaders
- **Version** with DVC and Git-LFS integration
- **Reproduce** builds from manifests

### The Dataset Pipeline

```
┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
│  Fetch  │ -> │Normalize│ -> │Validate │ -> │  Split  │ -> │ Export  │
└─────────┘    └─────────┘    └─────────┘    └─────────┘    └─────────┘
     │              │              │              │              │
     ▼              ▼              ▼              ▼              ▼
  HuggingFace   Parquet/CSV    Quality       Train/Val    PyTorch/TF
  Kaggle        JSONL          Checks        Test         JAX/DVC/LFS
  OpenML        Arrow
  Local Files
```

---

## Why Use mldata-cli?

| Challenge | mldata-cli Solution |
|-----------|---------------------|
| Multiple data sources | Single CLI for HF, Kaggle, OpenML, local files |
| Data quality issues | Built-in validation with detailed reports |
| Format incompatibility | Automatic conversion between Parquet, CSV, JSONL |
| Reproducibility | Manifest-based builds with hash verification |
| Large file tracking | DVC and Git-LFS integration |
| Download interruptions | Automatic resume with state persistence |

---

## Installation

### From PyPI (Recommended)

```bash
pip install mldata-cli
```

### From Source

```bash
git clone https://github.com/NoeFlandre/mldata-cli.git
cd mldata-cli
pip install -e .
```

### Verify Installation

```bash
mldata version
# Output: mldata-cli version 0.4.0
```

---

## Quick Start

### 1. Search for Datasets

```bash
# Search across all sources
mldata search "sentiment analysis"

# Limit results and filter by source
mldata search "image classification" --limit 10 --source hf --modality image
```

### 2. Build a Dataset (Full Pipeline)

```bash
# From HuggingFace with automatic splitting
mldata build hf://stanfordnlp/imdb \
    --output ./imdb \
    --format parquet \
    --split 0.8,0.1,0.1 \
    --seed 42

# From local file
mldata build ./data.csv \
    --output ./dataset \
    --format parquet \
    --seed 42
```

### 3. Validate Data Quality

```bash
# Run all quality checks
mldata validate ./imdb --checks all

# Generate a report
mldata validate ./imdb --checks all --report ./validation.md

# Check file integrity (images/audio)
mldata validate ./images --checks files
mldata validate ./images --checks files --sample 10  # Sample 10%
```

### 4. Export for Your Framework

```bash
# Export to multiple formats
mldata export ./imdb --formats parquet,csv,jsonl

# Generate PyTorch loader code
mldata export ./imdb --framework pytorch

# Configure version control
mldata export ./imdb --dvc --git-lfs
```

---

## Core Concepts

### Dataset Sources

mldata-cli supports multiple data sources through URI schemes:

| Source | URI Scheme | Example |
|--------|------------|---------|
| HuggingFace | `hf://` | `hf://stanfordnlp/imdb` |
| Kaggle | `kaggle://` | `kaggle://mnist` |
| OpenML | `openml://` | `openml://123` |
| Local Files | Path | `./data.csv`, `/path/data.parquet` |

### Build Outputs

A built dataset includes:

```
dataset/
├── manifest.yaml          # Build provenance & parameters
├── artifacts/
│   └── data.parquet      # Normalized dataset
├── splits/
│   ├── train.parquet
│   ├── val.parquet
│   └── test.parquet
└── raw/                  # Original files (optional)
```

### Manifest

The `manifest.yaml` tracks everything for reproducibility:

```yaml
mldata_version: 0.4.0
created_at: 2024-01-29T12:00:00Z
source:
  uri: hf://stanfordnlp/imdb
build:
  format: parquet
  split_ratios: [0.8, 0.1, 0.1]
  seed: 42
provenance:
  artifact_hashes:
    artifacts/data.parquet: sha256:abc123...
```

---

## Commands Reference

### search — Discover Datasets

Search across all supported sources.

```bash
mldata search "sentiment analysis" --limit 10 --source hf
```

| Option | Description |
|--------|-------------|
| `-n, --limit` | Maximum results (default: 20) |
| `-s, --source` | Filter by source (hf, kaggle, openml) |
| `-m, --modality` | Filter by modality (text, image, audio, tabular) |
| `-t, --task` | Filter by task (classification, regression) |

---

### info — Dataset Details

Show detailed information about a dataset.

```bash
mldata info hf://stanfordnlp/imdb
mldata info ./data.csv --schema
```

| Option | Description |
|--------|-------------|
| `-s, --sample` | Number of sample rows (default: 5) |
| `--schema/--no-schema` | Show/hide schema table |

---

### pull — Download Only

Download a dataset without processing.

```bash
mldata pull hf://stanfordnlp/imdb --output ./data
mldata pull hf://dataset --revision v1.0
```

**Feature: Download Resume**
- Interrupted downloads automatically resume
- State stored in `~/.mldata/resume/`
- ETA and speed displayed during download

---

### build — Full Pipeline

Fetch, normalize, validate, split, and export in one command.

```bash
# Complete pipeline
mldata build hf://stanfordnlp/imdb \
    --output ./imdb \
    --format parquet \
    --split 0.8,0.1,0.1 \
    --seed 42 \
    --stratify label

# With incremental builds (skip unchanged files)
mldata build ./data.csv \
    --output ./dataset \
    --incremental
```

| Option | Description |
|--------|-------------|
| `-o, --output` | Output directory |
| `-f, --format` | Output format (parquet, csv, jsonl) |
| `-s, --split` | Split ratios (default: 0.8,0.1,0.1) |
| `--seed` | Random seed for reproducibility |
| `--stratify` | Column for stratified splitting |
| `--validate/--no-validate` | Run quality checks |
| `--incremental` | Skip unchanged files (v0.4.0) |
| `--no-cache` | Skip cache |

---

### validate — Quality Checks

Run data quality validation with detailed reports.

```bash
# All checks
mldata validate ./imdb --checks all

# Specific checks
mldata validate ./imdb --checks duplicates,labels,missing,schema

# File integrity (images/audio)
mldata validate ./images --checks files
mldata validate ./images --checks files --sample 10

# Generate report
mldata validate ./imdb --checks all --report ./report.md
mldata validate ./imdb --checks all --report ./report.json
```

| Check | Description |
|-------|-------------|
| `duplicates` | Find duplicate rows |
| `labels` | Analyze label distribution |
| `missing` | Detect missing values |
| `schema` | Validate type consistency |
| `files` | Validate image/audio file integrity (v0.4.0) |

| Option | Description |
|--------|-------------|
| `-c, --checks` | Comma-separated checks |
| `-r, --report` | Output report path |
| `--json` | JSON output to stdout |
| `-s, --sample` | Sample % for file checks |

---

### profile — Statistics

Generate dataset statistics and profiles.

```bash
# Full profile
mldata profile ./data.csv

# Schema only
mldata profile ./data.csv --no-stats

# Export report
mldata profile ./data.csv --output ./profile.json
mldata profile ./data.csv --output ./profile.md
```

| Option | Description |
|--------|-------------|
| `-o, --output` | Output path (.json or .md) |
| `--stats/--no-stats` | Show/hide statistics |
| `--schema/--no-schema` | Show/hide schema |
| `-s, --sample` | Sample rows to show |

---

### drift — Detect Data Drift

Compare datasets using Population Stability Index (PSI).

```bash
# Basic comparison
mldata drift ./baseline ./current

# Detailed output
mldata drift ./baseline ./current --detailed

# Export report
mldata drift ./baseline ./current --output ./drift.json
```

| Option | Description |
|--------|-------------|
| `-o, --output` | Output report path |
| `-d, --detailed` | Show detailed statistics |

**Severity Levels:**
- `low`: PSI < 0.1 (no action needed)
- `medium`: 0.1 <= PSI < 0.2 (monitor)
- `high`: PSI >= 0.2 (investigate)

---

### split — Create Splits

Split datasets into train/val/test sets.

```bash
# Basic split
mldata split ./data.csv 0.8,0.1,0.1 --output ./splits

# With stratification
mldata split ./data.csv 0.8,0.1,0.1 --output ./splits --stratify label

# With seed for reproducibility
mldata split ./data.csv 0.8,0.1,0.1 --output ./splits --seed 42

# Save indices
mldata split ./data.csv 0.8,0.1,0.1 --output ./splits --indices
```

| Option | Description |
|--------|-------------|
| `-o, --output` | Output directory |
| `--seed` | Random seed |
| `--stratify` | Column for stratified split |
| `-f, --format` | Output format |
| `-i, --indices` | Save split indices |

---

### export — Export Dataset

Export datasets to various formats with optional integrations.

```bash
# Single format
mldata export ./imdb --format parquet

# Multiple formats
mldata export ./imdb --formats parquet,csv,jsonl

# All formats
mldata export ./imdb --all

# With compression
mldata export ./imdb --compression gzip:6
mldata export ./imdb --compression zstd:3

# Framework loaders (v0.4.0)
mldata export ./imdb --framework pytorch
mldata export ./imdb --framework tensorflow
mldata export ./imdb --framework jax

# Version control (v0.4.0)
mldata export ./imdb --dvc
mldata export ./imdb --git-lfs

# All features combined
mldata export ./imdb \
    --formats parquet,csv,jsonl \
    --framework pytorch \
    --dvc \
    --git-lfs
```

| Option | Description |
|--------|-------------|
| `-f, --format` | Single format (parquet, csv, jsonl) |
| `--formats` | Multiple formats (comma-separated) |
| `-o, --output` | Output directory |
| `-a, --all` | Export to all formats |
| `--compression` | Compression with optional level |
| `--framework` | Framework loader (pytorch, tensorflow, jax) |
| `--dvc` | Generate DVC file |
| `--git-lfs` | Configure Git-LFS |

**Compression Options:**

| Type | Level | Speed | Ratio | Best For |
|------|-------|-------|-------|----------|
| snappy | No | Fastest | 2-3x | Performance |
| gzip | 1-9 | Medium | 3-5x | Compatibility |
| zstd | 1-22 | Fast | 4-7x | Best ratio |
| lz4 | No | Very Fast | 2x | Minimal latency |

---

### diff — Compare Builds

Compare two dataset builds.

```bash
# Basic comparison
mldata diff ./build1 ./build2

# Detailed comparison
mldata diff ./build1 ./build2 --detailed

# With drift detection
mldata diff ./build1 ./build2 --drift

# Schema evolution
mldata diff ./build1 ./build2 --schema
```

| Option | Description |
|--------|-------------|
| `-d, --data/--no-data` | Compare actual data |
| `-m, --manifest/--no-manifest` | Compare parameters |
| `--drift` | Detect data drift |
| `--schema` | Show schema evolution |
| `-D, --detailed` | Show detailed differences |

---

### rebuild — Reproduce Builds

Rebuild a dataset from its manifest.

```bash
# Rebuild from manifest
mldata rebuild ./imdb/manifest.yaml --output ./imdb-rebuilt

# Preview without executing
mldata rebuild ./imdb/manifest.yaml --dry-run

# Skip verification
mldata rebuild ./imdb/manifest.yaml --no-verify
```

| Option | Description |
|--------|-------------|
| `-o, --output` | Output directory |
| `-v, --verify/--no-verify` | Verify against manifest |
| `-n, --dry-run` | Preview without executing |

---

### auth — Authentication

Manage credentials for data sources.

```bash
# Show authentication status
mldata auth status

# Login to sources
mldata auth login hf
mldata auth login kaggle
mldata auth login openml

# Logout
mldata auth logout hf
```

---

### config — Configuration

View and modify configuration.

```bash
# Show all configuration
mldata config --show

# Get a value
mldata config --get build.default_format

# Set a value
mldata config --set build.default_format csv

# Show config file path
mldata config --path
```

**Config Locations (priority order):**
1. `./mldata.yaml` (project)
2. `~/.config/mldata.yaml` (user)
3. `~/.mldata.yaml` (legacy)

**Common Settings:**

```yaml
build:
  default_format: parquet      # Default export format
  default_split: 0.8,0.1,0.1   # Default split ratios
  workers: 4                   # Parallel workers
  compression: zstd            # Default compression

cache:
  max_size_gb: 10              # Cache size limit
  ttl_hours: 168               # Cache TTL (7 days)
```

---

### doctor — Health Check

Diagnose configuration and connectivity issues.

```bash
mldata doctor
```

Checks:
- Authentication status
- Cache directory
- Network connectivity
- Dependencies

---

### version — Version Info

```bash
mldata version
# Output: mldata-cli version 0.4.0
```

---

## Data Sources

### HuggingFace

```bash
# By dataset name
mldata pull hf://stanfordnlp/imdb

# With revision
mldata pull hf://dataset --revision v1.0

# Build with full pipeline
mldata build hf://stanfordnlp/imdb --output ./imdb
```

**Environment:** `HUGGINGFACE_TOKEN`

### Kaggle

```bash
# By dataset name
mldata pull kaggle://mnist

# Build with full pipeline
mldata build kaggle://titanic --output ./titanic
```

**Environment:** `KAGGLE_USERNAME`, `KAGGLE_KEY`

### OpenML

```bash
# By dataset ID
mldata pull openml://31  # MNIST

# Build with full pipeline
mldata build openml://31 --output ./mnist
```

**Environment:** `OPENML_API_KEY`

### Local Files

```bash
# Single file
mldata build ./data.csv --output ./dataset

# Directory
mldata build ./data/ --output ./dataset

# Glob pattern
mldata build ./data/*.csv --output ./dataset

# Recursive glob
mldata build ./data/**/*.parquet --output ./dataset
```

---

## Output Formats

### Supported Formats

| Format | Extension | Description |
|--------|-----------|-------------|
| Parquet | `.parquet` | Columnar storage, recommended |
| CSV | `.csv` | comma-separated values |
| JSONL | `.jsonl` | JSON Lines (one JSON per line) |
| JSON | `.json` | Standard JSON array |

### Compression

| Compression | Extensions | Level Support |
|-------------|------------|---------------|
| Snappy | `.parquet.snappy` | None (fastest) |
| Gzip | `.parquet.gz`, `.csv.gz` | 1-9 |
| Zstd | `.parquet.zst`, `.csv.zst` | 1-22 |
| LZ4 | `.parquet.lz4` | None (very fast) |

---

## Advanced Features

### Incremental Builds (v0.4.0)

Skip reprocessing unchanged files:

```bash
mldata build ./data.csv --output ./dataset --incremental

# First run: Processes all files
# Subsequent runs: Skips unchanged files
```

**How it works:**
1. Computes SHA-256 hash of each file
2. Compares with cached hashes
3. Skips files that haven't changed
4. Shows "Processed: X, Skipped: Y" summary

---

### File Integrity Checks (v0.4.0)

Validate image and audio files:

```bash
# Check all image files
mldata validate ./images --checks files

# Sample 10% of files (for large datasets)
mldata validate ./images --checks files --sample 10

# Check audio files
mldata validate ./audio --checks files

# Combined with data quality checks
mldata validate ./dataset --checks duplicates,labels,missing,schema,files
```

**Supported Formats:**
- Images: JPEG, PNG, GIF, BMP, WebP, TIFF
- Audio: WAV, MP3, FLAC, OGG, M4A, AAC

---

### DVC Integration (v0.4.0)

Generate DVC files for dataset versioning:

```bash
mldata export ./imdb --dvc
```

This creates:
- `imdb.dvc` - DVC tracking file
- Instructions for pushing to remote

**Output:**
```
Generated: imdb.dvc
→ Run 'dvc push' to upload to remote storage
```

**DVC File Format:**
```yaml
outs:
- cache: true
  md5: <hash>
  path: imdb
```

---

### Git-LFS Integration (v0.4.0)

Configure Git-LFS for large files:

```bash
mldata export ./imdb --git-lfs
```

This:
- Creates/updates `.gitattributes`
- Adds patterns for: *.parquet, *.csv, *.jsonl, *.arrow, *.feather

**Generated .gitattributes:**
```gitattributes
# Git-LFS patterns for mldata-cli

*.parquet filter=lfs diff=lfs merge=lfs -text
*.csv filter=lfs diff=lfs merge=lfs -text
*.jsonl filter=lfs diff=lfs merge=lfs -text
*.arrow filter=lfs diff=lfs merge=lfs -text
*.feather filter=lfs diff=lfs merge=lfs -text
```

---

### Framework Templates (v0.4.0)

Export with ready-to-use framework loaders:

```bash
# PyTorch
mldata export ./imdb --framework pytorch
# Output: pytorch_dataset.py + data.parquet

# TensorFlow
mldata export ./imdb --framework tensorflow
# Output: tensorflow_dataset.py + data.parquet

# JAX
mldata export ./imdb --framework jax
# Output: jax_dataset.py + train.npz, val.npz, test.npz
```

**Generated Code Example (PyTorch):**
```python
from pytorch_dataset import IMDBDataset
from torch.utils.data import DataLoader

dataset = IMDBDataset("./data/parquet")
loader = DataLoader(dataset, batch_size=32)

for batch in loader:
    print(batch["text"], batch["label"])
```

---

## Configuration

### Environment Variables

| Variable | Description |
|----------|-------------|
| `HUGGINGFACE_TOKEN` | HuggingFace API token |
| `KAGGLE_USERNAME` | Kaggle username |
| `KAGGLE_KEY` | Kaggle API key |
| `OPENML_API_KEY` | OpenML API key |

### Cache Location

- **Unix/Linux:** `~/.mldata/cache/`
- **macOS:** `~/.mldata/cache/`
- **Windows:** `%USERPROFILE%\.mldata\cache\`

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Build failure |
| 2 | Validation failure |
| 3 | Config error |
| 4 | Auth error |
| 5 | Network error |
| 130 | User cancelled (Ctrl+C) |

---

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## License

MIT License - see LICENSE file for details.

---

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for detailed release notes.
