# mldata-cli — Technical Design Document

## Document Control

| Field | Value |
|-------|-------|
| **Version** | 1.0 |
| **Date** | 2026-01-29 |
| **Author** | Noé Flandre |
| **Status** | Draft |
| **Parent Document** | [PRD](./PRD.md), [Epic List](./epic-list.md) |

---

## 1. Architecture Overview

### 1.1 System Context

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              User Environment                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌─────────────┐     ┌─────────────┐     ┌─────────────┐                  │
│   │   Terminal  │     │     CI      │     │   Scripts   │                  │
│   └──────┬──────┘     └──────┬──────┘     └──────┬──────┘                  │
│          │                   │                   │                          │
│          └───────────────────┼───────────────────┘                          │
│                              │                                              │
│                              ▼                                              │
│                    ┌─────────────────┐                                      │
│                    │   mldata CLI    │                                      │
│                    └────────┬────────┘                                      │
│                             │                                               │
└─────────────────────────────┼───────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           mldata-cli Core                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌───────────────────────────────────────────────────────────────────┐    │
│   │                        CLI Layer (Typer + Rich)                    │    │
│   │   Commands: search, pull, build, validate, split, export, etc.    │    │
│   └───────────────────────────────────────────────────────────────────┘    │
│                              │                                              │
│   ┌───────────────────────────────────────────────────────────────────┐    │
│   │                         Core Services                              │    │
│   │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐     │    │
│   │  │ Search  │ │  Fetch  │ │Normalize│ │Validate │ │  Split  │     │    │
│   │  └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘     │    │
│   │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐                 │    │
│   │  │ Export  │ │ Manifest│ │  Cache  │ │  Auth   │                 │    │
│   │  └─────────┘ └─────────┘ └─────────┘ └─────────┘                 │    │
│   └───────────────────────────────────────────────────────────────────┘    │
│                              │                                              │
│   ┌───────────────────────────────────────────────────────────────────┐    │
│   │                      Connector Layer                               │    │
│   │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐          │    │
│   │  │HuggingFace│  │  Kaggle  │  │  OpenML  │  │  Local   │          │    │
│   │  │Connector │  │Connector │  │Connector │  │Connector │          │    │
│   │  └──────────┘  └──────────┘  └──────────┘  └──────────┘          │    │
│   └───────────────────────────────────────────────────────────────────┘    │
│                              │                                              │
│   ┌───────────────────────────────────────────────────────────────────┐    │
│   │                       Storage Layer                                │    │
│   │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐               │    │
│   │  │   Cache     │  │  Artifacts  │  │   Config    │               │    │
│   │  │(~/.mldata/) │  │ (./mldata/) │  │(mldata.yaml)│               │    │
│   │  └─────────────┘  └─────────────┘  └─────────────┘               │    │
│   └───────────────────────────────────────────────────────────────────┘    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          External Services                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│   ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐                   │
│   │HuggingFace│  │  Kaggle  │  │  OpenML  │  │   DVC    │                   │
│   │   Hub    │  │   API    │  │   API    │  │  Remote  │                   │
│   └──────────┘  └──────────┘  └──────────┘  └──────────┘                   │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Technology Stack

| Layer | Technology | Rationale |
|-------|------------|-----------|
| **CLI Framework** | Typer | Type-safe, auto-generated help, modern Python |
| **Terminal UI** | Rich | Beautiful output, progress bars, tables |
| **Data Processing** | Polars | Fast DataFrame operations, lazy evaluation |
| **SQL Queries** | DuckDB | Embedded analytics, Parquet native |
| **HTTP Client** | httpx | Async support, modern API |
| **Caching** | diskcache | Simple, reliable file-based cache |
| **Auth Storage** | keyring | OS-native credential storage |
| **Config** | Pydantic | Validation, serialization, settings |
| **Package Manager** | uv | Fast, reliable dependency management |
| **Testing** | pytest + VCR.py | Unit tests + API mocking |

### 1.3 Project Structure

```
mldata-cli/
├── pyproject.toml          # uv project config
├── uv.lock                  # Locked dependencies
├── README.md
├── LICENSE
├── docs/
│   ├── product-vision.md
│   ├── PRD.md
│   ├── epic-list.md
│   ├── technical-design.md  # This document
│   └── ...
├── src/
│   └── mldata/
│       ├── __init__.py
│       ├── __main__.py      # Entry point
│       ├── cli/
│       │   ├── __init__.py
│       │   ├── main.py      # Typer app
│       │   ├── search.py    # mldata search
│       │   ├── pull.py      # mldata pull
│       │   ├── build.py     # mldata build
│       │   ├── validate.py  # mldata validate
│       │   ├── split.py     # mldata split
│       │   ├── export.py    # mldata export
│       │   ├── rebuild.py   # mldata rebuild
│       │   ├── diff.py      # mldata diff
│       │   ├── auth.py      # mldata auth
│       │   └── doctor.py    # mldata doctor
│       ├── core/
│       │   ├── __init__.py
│       │   ├── search.py    # Search service
│       │   ├── fetch.py     # Download service
│       │   ├── normalize.py # Normalization service
│       │   ├── validate.py  # Validation service
│       │   ├── split.py     # Splitting service
│       │   ├── export.py    # Export service
│       │   ├── manifest.py  # Manifest handling
│       │   └── cache.py     # Cache management
│       ├── connectors/
│       │   ├── __init__.py
│       │   ├── base.py      # Abstract connector
│       │   ├── huggingface.py
│       │   ├── kaggle.py
│       │   ├── openml.py
│       │   └── local.py
│       ├── checks/
│       │   ├── __init__.py
│       │   ├── base.py      # Abstract check
│       │   ├── duplicates.py
│       │   ├── labels.py
│       │   ├── missing.py
│       │   ├── schema.py
│       │   └── files.py
│       ├── models/
│       │   ├── __init__.py
│       │   ├── dataset.py   # Dataset metadata
│       │   ├── manifest.py  # Manifest schema
│       │   ├── report.py    # Quality report
│       │   └── config.py    # Configuration
│       └── utils/
│           ├── __init__.py
│           ├── auth.py      # Auth utilities
│           ├── hashing.py   # SHA-256 utilities
│           ├── logging.py   # Structured logging
│           └── progress.py  # Rich progress
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── unit/
│   ├── integration/
│   └── e2e/
└── fixtures/               # Test datasets
```

---

## 2. CLI Command Reference

### 2.1 Command Overview

```
mldata <command> [options]

Commands:
  search      Search for datasets across sources
  info        Display detailed dataset information
  pull        Download a dataset
  build       Full pipeline: fetch, normalize, validate, split, export
  validate    Run quality checks on a dataset
  split       Generate train/val/test splits
  export      Export dataset to specific format
  rebuild     Rebuild dataset from manifest
  diff        Compare two dataset builds
  auth        Manage authentication
  doctor      Diagnose configuration issues
  config      Manage configuration

Global Options:
  --json          Output in JSON format (machine-readable)
  --quiet, -q     Suppress non-essential output
  --verbose, -v   Increase output verbosity
  --no-cache      Bypass cache for this operation
  --config FILE   Use specific config file
  --version       Show version and exit
  --help          Show help and exit
```

### 2.2 Command Details

#### `mldata search`

Search for datasets across configured sources.

```
mldata search <query> [options]

Arguments:
  query              Search query string

Options:
  --source, -s       Filter by source (hf, kaggle, openml, all)
  --modality, -m     Filter by data modality (text, image, audio, tabular)
  --task, -t         Filter by ML task (classification, regression, etc.)
  --limit, -n        Maximum results to return (default: 20)
  --min-size         Minimum dataset size
  --max-size         Maximum dataset size
  --license          Filter by license type

Examples:
  mldata search "sentiment analysis" --modality text
  mldata search "image classification" --source kaggle --limit 10
  mldata search "tabular" --task regression --max-size 1GB
```

#### `mldata info`

Display detailed information about a dataset.

```
mldata info <uri> [options]

Arguments:
  uri                Dataset URI (hf://owner/name, kaggle://owner/name, etc.)

Options:
  --fields           Specific fields to display
  --schema           Show schema/column information
  --sample           Show sample rows (default: 5)

Examples:
  mldata info hf://stanfordnlp/imdb
  mldata info kaggle://mnist --schema --sample 10
```

#### `mldata pull`

Download a dataset from a source.

```
mldata pull <uri> [options]

Arguments:
  uri                Dataset URI

Options:
  --output, -o       Output directory (default: ./mldata/<name>)
  --format, -f       Convert to format (csv, jsonl, parquet)
  --revision, -r     Specific version/revision
  --subset           Download specific subset/config
  --no-cache         Force fresh download

Examples:
  mldata pull hf://stanfordnlp/imdb --output ./data/imdb
  mldata pull kaggle://mnist --format parquet
  mldata pull openml://iris --revision 1
```

#### `mldata build`

Full pipeline: fetch, normalize, validate, split, export.

```
mldata build <uri> [options]

Arguments:
  uri                Dataset URI

Options:
  --output, -o       Output directory
  --config, -c       Build configuration file
  --format, -f       Export format(s) (csv, jsonl, parquet)
  --split            Split ratios (default: 0.8,0.1,0.1)
  --seed             Random seed for reproducibility
  --stratify         Column to stratify splits on
  --validate         Validation checks to run (all, none, or specific)
  --no-cache         Bypass cache

Examples:
  mldata build hf://stanfordnlp/imdb --format parquet --stratify label
  mldata build kaggle://mnist --config mldata.yaml
  mldata build openml://iris --split 0.7,0.15,0.15 --seed 42
```

#### `mldata validate`

Run quality checks on a dataset.

```
mldata validate <path> [options]

Arguments:
  path               Path to dataset directory or file

Options:
  --checks           Checks to run (all, duplicates, labels, missing, schema, files)
  --report, -r       Report output path
  --format           Report format (json, markdown, both)
  --threshold        Duplicate similarity threshold (0.0-1.0)
  --fail-on          Fail if issues found (errors, warnings, none)

Examples:
  mldata validate ./data/mnist --checks all --report ./reports/
  mldata validate ./data/imdb --checks duplicates,labels --fail-on errors
```

#### `mldata split`

Generate train/val/test splits.

```
mldata split <path> [options]

Arguments:
  path               Path to dataset

Options:
  --ratios           Split ratios (default: 0.8,0.1,0.1)
  --seed             Random seed for reproducibility
  --stratify         Column to stratify on
  --group            Column for group-aware splitting
  --output, -o       Output directory for split files

Examples:
  mldata split ./data/mnist --ratios 0.7,0.15,0.15 --stratify label
  mldata split ./data/users --group user_id --seed 42
```

#### `mldata export`

Export dataset to specific format.

```
mldata export <path> [options]

Arguments:
  path               Path to dataset

Options:
  --format, -f       Output format (csv, jsonl, parquet, arrow)
  --output, -o       Output path
  --compression      Compression (none, gzip, snappy, zstd)
  --split            Export specific split (train, val, test, all)

Examples:
  mldata export ./data/mnist --format parquet --compression snappy
  mldata export ./data/imdb --format jsonl --split train
```

#### `mldata rebuild`

Rebuild dataset from manifest.

```
mldata rebuild <manifest> [options]

Arguments:
  manifest           Path to manifest.yaml file

Options:
  --output, -o       Output directory
  --verify           Verify hashes after rebuild (default: true)
  --no-cache         Force fresh downloads

Examples:
  mldata rebuild ./data/mnist/manifest.yaml --output ./data/mnist-v2
  mldata rebuild manifest.yaml --verify --no-cache
```

#### `mldata diff`

Compare two dataset builds.

```
mldata diff <manifest1> <manifest2> [options]

Arguments:
  manifest1          First manifest or dataset path
  manifest2          Second manifest or dataset path

Options:
  --format           Output format (text, json)
  --detailed         Show row-level differences

Examples:
  mldata diff ./v1/manifest.yaml ./v2/manifest.yaml
  mldata diff ./data/old ./data/new --detailed
```

#### `mldata auth`

Manage authentication credentials.

```
mldata auth <subcommand> [options]

Subcommands:
  status             Show authentication status
  login <source>     Configure credentials for a source
  logout <source>    Remove credentials for a source

Options:
  --json             Output in JSON format

Examples:
  mldata auth status
  mldata auth login huggingface
  mldata auth logout kaggle
```

#### `mldata doctor`

Diagnose configuration and connectivity issues.

```
mldata doctor [options]

Options:
  --fix              Attempt to fix issues automatically
  --source           Check specific source only

Examples:
  mldata doctor
  mldata doctor --source kaggle --fix
```

---

## 3. Technical Contracts

### 3.1 Exit Codes

| Code | Name | Description | Usage |
|------|------|-------------|-------|
| 0 | SUCCESS | Operation completed successfully | Normal completion |
| 1 | BUILD_FAILURE | Build or operation failed | Download error, processing error |
| 2 | VALIDATION_FAILURE | Validation found issues | Quality check failures |
| 3 | CONFIG_ERROR | Configuration error | Invalid config, missing required fields |
| 4 | AUTH_ERROR | Authentication error | Missing/invalid credentials |
| 5 | NETWORK_ERROR | Network connectivity error | API unreachable, timeout |

### 3.2 Output Streams

| Stream | Content | Format |
|--------|---------|--------|
| **stdout** | Progress, summaries, results | Human-readable (default) or JSON (`--json`) |
| **stderr** | Errors, warnings, debug logs | Always text, prefixed by level |

### 3.3 JSON Mode (`--json`)

All commands support `--json` flag for machine-readable output:

```json
{
  "success": true,
  "command": "build",
  "version": "0.1.0",
  "timestamp": "2026-01-29T10:30:00Z",
  "duration_seconds": 45.2,
  "result": {
    "dataset": "hf://stanfordnlp/imdb",
    "output_path": "./mldata/imdb",
    "manifest_path": "./mldata/imdb/manifest.yaml",
    "artifacts": {
      "train": "./mldata/imdb/splits/train.parquet",
      "val": "./mldata/imdb/splits/val.parquet",
      "test": "./mldata/imdb/splits/test.parquet"
    },
    "quality_report": "./mldata/imdb/reports/quality.json"
  },
  "warnings": [],
  "errors": []
}
```

### 3.4 Determinism & Reproducibility Contract

**Guarantee:** Given the same manifest and inputs, mldata produces identical artifact hashes.

**Requirements captured in manifest:**
- Tool version (`mldata_version`)
- Python version (`python_version`)
- All dependency versions (locked in `uv.lock`)
- Random seed for splitting
- All processing parameters

**Hash algorithm:** SHA-256 for all artifact verification

**Verification:**
```bash
# Rebuild and verify
mldata rebuild manifest.yaml --verify

# Output includes hash comparison
✓ train.parquet: sha256:abc123... (match)
✓ val.parquet: sha256:def456... (match)
✓ test.parquet: sha256:ghi789... (match)
```

### 3.5 Caching Model

**Cache location:** `~/.mldata/cache/`

**Cache key formula:**
```
cache_key = SHA256(source_uri + version + fetch_params)
```

**Provenance chain:**
```
source → raw → intermediate → artifact
   │       │        │            │
   └───────┴────────┴────────────┴── Each step hashed
```

**Cache structure:**
```
~/.mldata/
├── cache/
│   ├── downloads/           # Raw downloaded files
│   │   └── {hash}/
│   ├── intermediate/        # Processed intermediates
│   │   └── {hash}/
│   └── metadata/            # Cached metadata
│       └── {source}/{dataset}.json
├── config.yaml              # Global configuration
└── auth/                    # Credential hints (not secrets)
```

**Cache invalidation:**
- TTL-based (configurable, default 7 days for metadata)
- Explicit: `--no-cache` flag
- Version change: new tool version invalidates processing cache

### 3.6 Auth & Secrets Handling

**Credential sources (priority order):**
1. Environment variables (`HUGGINGFACE_TOKEN`, `KAGGLE_KEY`, etc.)
2. System keyring (OS-native credential storage)
3. Config file (`~/.mldata/config.yaml`)

**Security requirements:**
- Secrets NEVER logged (automatic redaction)
- Config file permissions enforced (600)
- Tokens masked in `auth status` output

**Environment variables:**
```bash
# HuggingFace
export HUGGINGFACE_TOKEN=hf_xxxxx

# Kaggle
export KAGGLE_USERNAME=username
export KAGGLE_KEY=xxxxx

# OpenML
export OPENML_API_KEY=xxxxx
```

**Credential storage locations:**
| Source | Keyring Service | Env Var |
|--------|-----------------|---------|
| HuggingFace | `mldata-huggingface` | `HUGGINGFACE_TOKEN` |
| Kaggle | `mldata-kaggle` | `KAGGLE_USERNAME`, `KAGGLE_KEY` |
| OpenML | `mldata-openml` | `OPENML_API_KEY` |

### 3.7 Licensing & Attribution

**Requirements:**
- License field required in manifest for every dataset
- Attribution requirements captured per source
- Warning system for restrictive licenses (NC, research-only)

**License display:**
```bash
mldata info hf://dataset
# Output includes:
# License: Apache-2.0
# Attribution: Required (see dataset card)
# Commercial Use: Allowed
```

**Restrictive license handling:**
```bash
mldata pull kaggle://restricted-dataset
⚠ This dataset has a restrictive license: CC BY-NC-SA 4.0
  - Non-commercial use only
  - Share-alike required

Accept license terms? [y/N]:
```

---

## 4. Connector Interface

### 4.1 Abstract Base Class

```python
from abc import ABC, abstractmethod
from typing import AsyncIterator
from mldata.models import DatasetMetadata, SearchResult, DownloadProgress

class BaseConnector(ABC):
    """Abstract base class for dataset source connectors."""

    # Connector identification
    name: str  # e.g., "huggingface"
    uri_schemes: list[str]  # e.g., ["hf://", "huggingface://"]

    @abstractmethod
    async def search(
        self,
        query: str,
        *,
        modality: str | None = None,
        task: str | None = None,
        limit: int = 20,
    ) -> list[SearchResult]:
        """Search for datasets matching query."""
        ...

    @abstractmethod
    async def get_metadata(self, dataset_id: str) -> DatasetMetadata:
        """Get detailed metadata for a dataset."""
        ...

    @abstractmethod
    async def download(
        self,
        dataset_id: str,
        output_path: Path,
        *,
        revision: str | None = None,
        subset: str | None = None,
    ) -> AsyncIterator[DownloadProgress]:
        """Download dataset files, yielding progress updates."""
        ...

    @abstractmethod
    async def authenticate(self) -> bool:
        """Verify authentication is configured and valid."""
        ...

    @abstractmethod
    def parse_uri(self, uri: str) -> tuple[str, dict]:
        """Parse URI into dataset_id and parameters."""
        ...
```

### 4.2 Connector Registry

```python
from mldata.connectors import HuggingFaceConnector, KaggleConnector, OpenMLConnector

CONNECTORS = {
    "huggingface": HuggingFaceConnector,
    "hf": HuggingFaceConnector,
    "kaggle": KaggleConnector,
    "openml": OpenMLConnector,
}

def get_connector(uri: str) -> BaseConnector:
    """Get appropriate connector for URI."""
    scheme = uri.split("://")[0]
    if scheme not in CONNECTORS:
        raise ValueError(f"Unknown source: {scheme}")
    return CONNECTORS[scheme]()
```

---

## 5. Quality Check Interface

### 5.1 Abstract Check Class

```python
from abc import ABC, abstractmethod
from mldata.models import CheckResult, CheckSeverity

class BaseCheck(ABC):
    """Abstract base class for quality checks."""

    name: str  # e.g., "duplicates"
    description: str
    default_enabled: bool = True

    @abstractmethod
    def run(self, dataset_path: Path, config: dict) -> CheckResult:
        """Execute the check and return results."""
        ...

    @property
    @abstractmethod
    def configurable_params(self) -> dict:
        """Return configurable parameters with defaults."""
        ...

class CheckResult:
    """Result of a quality check."""
    check_name: str
    passed: bool
    severity: CheckSeverity  # INFO, WARNING, ERROR
    message: str
    details: dict  # Check-specific details
    suggestions: list[str]  # Remediation suggestions
```

### 5.2 Built-in Checks

| Check | Description | Configurable Params |
|-------|-------------|---------------------|
| `DuplicateCheck` | Detect exact and near-duplicate samples | `threshold`, `hash_columns` |
| `LabelDistributionCheck` | Analyze class imbalance | `imbalance_threshold`, `label_column` |
| `MissingValueCheck` | Detect missing/null values | `max_missing_ratio`, `columns` |
| `SchemaConsistencyCheck` | Validate schema across splits | `strict_types` |
| `FileIntegrityCheck` | Verify image/audio files are valid | `file_columns`, `check_corruption` |

---

## 6. Data Models

### 6.1 Manifest Schema (YAML)

```yaml
# manifest.yaml
mldata_version: "0.1.0"
created_at: "2026-01-29T10:30:00Z"
python_version: "3.11.0"

source:
  uri: "hf://stanfordnlp/imdb"
  revision: "main"
  subset: null
  fetched_at: "2026-01-29T10:25:00Z"

build:
  seed: 42
  split_ratios: [0.8, 0.1, 0.1]
  stratify_column: "label"
  format: "parquet"
  checks_enabled: ["duplicates", "labels", "missing", "schema"]

provenance:
  source_hash: "sha256:abc123..."
  raw_hash: "sha256:def456..."
  artifact_hashes:
    train: "sha256:111..."
    val: "sha256:222..."
    test: "sha256:333..."

dataset:
  name: "imdb"
  license: "Apache-2.0"
  size_bytes: 84000000
  num_samples: 50000
  splits:
    train: 40000
    val: 5000
    test: 5000
  schema:
    text: "string"
    label: "int64"

quality:
  checks_passed: true
  report_path: "reports/quality.json"
  issues_found: 2
  issues_by_severity:
    error: 0
    warning: 1
    info: 1

environment:
  os: "Linux"
  architecture: "x86_64"
  dependencies:
    polars: "0.20.0"
    pyarrow: "15.0.0"
```

### 6.2 Quality Report Schema (JSON)

```json
{
  "$schema": "https://mldata.dev/schemas/quality-report-v1.json",
  "version": "1.0",
  "generated_at": "2026-01-29T10:30:00Z",
  "dataset": {
    "path": "./mldata/imdb",
    "uri": "hf://stanfordnlp/imdb",
    "num_samples": 50000
  },
  "summary": {
    "total_checks": 5,
    "passed": 4,
    "failed": 1,
    "warnings": 1,
    "errors": 0
  },
  "checks": [
    {
      "name": "duplicates",
      "passed": true,
      "severity": "info",
      "message": "No exact duplicates found",
      "details": {
        "exact_duplicates": 0,
        "near_duplicates": 12,
        "threshold": 0.95
      },
      "duration_ms": 1234
    },
    {
      "name": "label_distribution",
      "passed": false,
      "severity": "warning",
      "message": "Class imbalance detected",
      "details": {
        "distribution": {
          "positive": 0.52,
          "negative": 0.48
        },
        "imbalance_ratio": 1.08
      },
      "suggestions": [
        "Consider using stratified sampling",
        "Apply class weights during training"
      ],
      "duration_ms": 89
    }
  ]
}
```

### 6.3 Configuration Schema

**Global config (`~/.mldata/config.yaml`):**

```yaml
# Global mldata configuration
version: 1

cache:
  directory: ~/.mldata/cache
  max_size_gb: 50
  ttl_days: 7

defaults:
  format: parquet
  split_ratios: [0.8, 0.1, 0.1]
  checks: [duplicates, labels, missing, schema]

connectors:
  huggingface:
    enabled: true
    # token stored in keyring
  kaggle:
    enabled: true
  openml:
    enabled: true

telemetry:
  enabled: false  # Opt-in only
```

**Project config (`mldata.yaml`):**

```yaml
# Project-level mldata configuration
version: 1

output_dir: ./data

datasets:
  imdb:
    uri: hf://stanfordnlp/imdb
    format: parquet
    split_ratios: [0.8, 0.1, 0.1]
    stratify: label
    checks:
      duplicates:
        threshold: 0.95
      labels:
        imbalance_threshold: 0.1

  mnist:
    uri: kaggle://mnist
    format: parquet
    seed: 42
```

---

## 7. Architecture Decision Records (ADRs)

### ADR-001: CLI Framework Selection

**Status:** Accepted

**Context:**
We need a CLI framework for mldata-cli that supports:
- Type-safe argument parsing
- Auto-generated help text
- Rich terminal output
- Async command support
- Good developer experience

**Options Considered:**
1. **Click** - Mature, widely used, decorator-based
2. **Typer** - Built on Click, type hints for args, modern
3. **argparse** - Standard library, verbose
4. **Fire** - Auto-generates CLI from functions, less control

**Decision:**
Use **Typer** with **Rich** for terminal output.

**Rationale:**
- Typer leverages type hints for argument parsing (less boilerplate)
- Built on Click's solid foundation
- Native Rich integration for beautiful output
- Strong async support via `asyncio`
- Excellent developer experience with IDE support

**Consequences:**
- Requires Python 3.9+
- Team needs to learn Typer conventions
- Rich dependency adds to install size

---

### ADR-002: Data Processing Library Selection

**Status:** Accepted

**Context:**
We need a data processing library that can:
- Handle large datasets efficiently
- Support multiple formats (CSV, JSON, Parquet)
- Enable SQL-like queries for validation
- Work well in memory-constrained environments

**Options Considered:**
1. **Pandas** - Ubiquitous, large ecosystem, memory-heavy
2. **Polars** - Fast, lazy evaluation, Rust-based
3. **DuckDB** - SQL-native, excellent Parquet support
4. **PyArrow** - Low-level, great for formats, less ergonomic

**Decision:**
Use **Polars** for DataFrame operations and **DuckDB** for SQL queries.

**Rationale:**
- Polars is significantly faster than Pandas (10-100x for many operations)
- Lazy evaluation prevents loading full datasets into memory
- DuckDB provides SQL interface for complex validation queries
- Both have excellent Parquet support
- Polars has good pandas compatibility for gradual adoption

**Consequences:**
- Smaller ecosystem than Pandas
- Team needs to learn Polars API
- Some edge cases may need PyArrow directly

---

### ADR-003: Connector Plugin Architecture

**Status:** Accepted

**Context:**
We need to support multiple data sources (HuggingFace, Kaggle, OpenML) with:
- Consistent interface across sources
- Easy addition of new sources
- Source-specific optimizations
- Testability via mocking

**Options Considered:**
1. **Direct integration** - Hardcode each source
2. **Abstract base class** - Define interface, implement per source
3. **Plugin system** - Dynamic loading via entry points
4. **Strategy pattern** - Runtime selection of implementation

**Decision:**
Use **Abstract Base Class** with a **Connector Registry**.

**Rationale:**
- ABC provides clear contract for all connectors
- Registry pattern enables easy source lookup by URI
- Simpler than full plugin system for MVP
- Can evolve to entry-point plugins later
- Easy to test with mock connectors

**Consequences:**
- New connectors require code changes (not just config)
- Acceptable for MVP; plugin system can be added later
- Clear extension pattern for contributors

---

## 8. Traceability

| Component | Traces To |
|-----------|-----------|
| CLI Commands | PRD Functional Requirements, User Stories |
| Exit Codes | CI Contract (Plan §CI Contracts) |
| Connectors | Epic E2 (Fetch), Stories US-005 to US-010 |
| Quality Checks | Epic E4 (Validate), Stories US-016 to US-021 |
| Manifest Schema | Epic E7 (Rebuild), Determinism Contract |
| Cache Model | Caching Contract (Plan §3) |

---

**End of Document**
