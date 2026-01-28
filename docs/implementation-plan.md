# mldata-cli — Implementation Plan

## Document Control

| Field | Value |
|-------|-------|
| **Version** | 1.0 |
| **Date** | 2026-01-29 |
| **Author** | Noé Flandre |
| **Status** | Draft |
| **Parent Document** | [Sprint Backlog](./sprint-backlog.md) |

---

## Implementation Phases

### Phase Overview

| Phase | Sprints | Focus | Key Deliverables |
|-------|---------|-------|------------------|
| **1: Foundation** | 1-2 | CLI skeleton, auth, search, caching | Working CLI with discovery and download |
| **2: Core Pipeline** | 3-4 | Normalization, validation, splitting, export | Full build pipeline |
| **3: Full MVP** | 5-6 | Polish, rebuild, advanced features | Release-ready v0.1.0 |

---

## Phase 1: Foundation (Sprints 1-2)

### Goals
- Establish project structure and CI/CD
- Implement basic CLI commands
- Enable dataset download from 3 sources
- Implement authentication and caching

### Deliverables

| Deliverable | Sprint | Acceptance |
|-------------|--------|------------|
| Project scaffolding | 1 | uv project builds, CI passes |
| `mldata pull` command | 1 | Downloads from HF/Kaggle/OpenML |
| `mldata auth` commands | 1 | Credentials stored securely |
| `mldata search` command | 2 | Returns results from all sources |
| `mldata info` command | 2 | Shows detailed metadata |
| Content-addressed cache | 2 | Cache hits avoid network |

### Technical Setup Tasks

#### 1. Initialize Project

```bash
# Create project with uv
uv init mldata-cli
cd mldata-cli

# Set up pyproject.toml with dependencies
# Python 3.9+ target
```

**pyproject.toml structure:**
```toml
[project]
name = "mldata-cli"
version = "0.1.0"
description = "Unified CLI for ML dataset acquisition and preparation"
readme = "README.md"
requires-python = ">=3.9"
license = {text = "MIT"}
authors = [
    {name = "Noé Flandre", email = "noe@example.com"}
]
keywords = ["machine-learning", "datasets", "cli", "ml", "data"]
classifiers = [
    "Development Status :: 3 - Alpha",
    "Environment :: Console",
    "Intended Audience :: Developers",
    "Intended Audience :: Science/Research",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Topic :: Scientific/Engineering :: Artificial Intelligence",
]

dependencies = [
    "typer[all]>=0.9.0",
    "rich>=13.0.0",
    "polars>=0.20.0",
    "duckdb>=0.9.0",
    "httpx>=0.25.0",
    "keyring>=24.0.0",
    "pydantic>=2.0.0",
    "pyyaml>=6.0",
    "diskcache>=5.6.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-cov>=4.0.0",
    "pytest-asyncio>=0.21.0",
    "vcrpy>=5.0.0",
    "ruff>=0.1.0",
    "mypy>=1.0.0",
    "pre-commit>=3.0.0",
]

[project.scripts]
mldata = "mldata.cli.main:app"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.ruff]
line-length = 100
target-version = "py39"
select = ["E", "F", "I", "N", "W", "UP"]

[tool.mypy]
python_version = "3.9"
strict = true

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

#### 2. Configure Pre-commit Hooks

**.pre-commit-config.yaml:**
```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.6
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.7.0
    hooks:
      - id: mypy
        additional_dependencies: [types-PyYAML, types-requests]

  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
```

#### 3. Set Up GitHub Actions CI

**.github/workflows/ci.yml:**
```yaml
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, macos-latest]
        python-version: ["3.9", "3.10", "3.11", "3.12"]

    steps:
      - uses: actions/checkout@v4

      - name: Install uv
        uses: astral-sh/setup-uv@v1

      - name: Set up Python ${{ matrix.python-version }}
        run: uv python install ${{ matrix.python-version }}

      - name: Install dependencies
        run: uv sync --all-extras

      - name: Run linting
        run: uv run ruff check .

      - name: Run type checking
        run: uv run mypy src/

      - name: Run tests
        run: uv run pytest --cov=mldata --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml

  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Install uv
        uses: astral-sh/setup-uv@v1
      - run: uv sync --all-extras
      - run: uv run ruff check .
      - run: uv run ruff format --check .
```

---

## Phase 2: Core Pipeline (Sprints 3-4)

### Goals
- Implement data normalization and format conversion
- Build quality validation framework
- Create deterministic splitting
- Generate manifests and quality reports

### Deliverables

| Deliverable | Sprint | Acceptance |
|-------------|--------|------------|
| Format conversion (CSV/JSON/Parquet) | 3 | Lossless conversion |
| Standardized directory layout | 3 | Consistent output structure |
| Train/val/test splitting | 3 | Configurable, deterministic |
| Manifest generation | 3 | Full provenance captured |
| Duplicate detection | 4 | Exact + near-duplicate |
| Label analysis | 4 | Imbalance detection |
| Quality reports | 4 | JSON + Markdown output |
| Parquet export | 4 | Compressed, efficient |
| Rebuild from manifest | 4 | Identical output verified |

### Key Implementation Details

#### Polars-Based Processing

```python
# Example: Format conversion with Polars
import polars as pl

def convert_to_parquet(input_path: Path, output_path: Path) -> None:
    """Convert various formats to Parquet."""
    # Lazy loading for large files
    if input_path.suffix == ".csv":
        df = pl.scan_csv(input_path)
    elif input_path.suffix == ".json":
        df = pl.scan_ndjson(input_path)
    else:
        raise ValueError(f"Unsupported format: {input_path.suffix}")

    # Write with compression
    df.sink_parquet(output_path, compression="snappy")
```

#### Quality Check Architecture

```python
# Example: Check plugin architecture
from abc import ABC, abstractmethod

class BaseCheck(ABC):
    name: str

    @abstractmethod
    def run(self, df: pl.LazyFrame) -> CheckResult:
        pass

class DuplicateCheck(BaseCheck):
    name = "duplicates"

    def run(self, df: pl.LazyFrame) -> CheckResult:
        # Efficient duplicate detection
        total = df.select(pl.count()).collect().item()
        unique = df.unique().select(pl.count()).collect().item()
        duplicates = total - unique

        return CheckResult(
            check_name=self.name,
            passed=duplicates == 0,
            details={"duplicate_count": duplicates}
        )
```

---

## Phase 3: Full MVP (Sprints 5-6)

### Goals
- Complete remaining MVP features
- Polish user experience
- Fix bugs and edge cases
- Prepare documentation and release

### Deliverables

| Deliverable | Sprint | Acceptance |
|-------------|--------|------------|
| Schema inference | 5 | Automatic type detection |
| Schema validation | 5 | Cross-split consistency |
| Stratified splitting | 5 | Preserves label distribution |
| Build verification | 5 | Hash comparison |
| Search filters | 6 | Source/modality/task filters |
| Download resume | 6 | Resume partial downloads |
| Documentation | 6 | Complete user guide |
| Release preparation | 6 | PyPI-ready |

---

## Development Workflow

### Branching Strategy

```
main          ─────●─────────────────●─────────────────●───── (releases)
                   │                 │                 │
develop       ─────●────●────●───────●────●────●───────●───── (integration)
                        │    │            │    │
feature/*              ─●────●           ─●────●              (features)
```

**Branch Types:**
- `main`: Stable releases only
- `develop`: Integration branch
- `feature/*`: Feature branches (e.g., `feature/us-005-download`)
- `fix/*`: Bug fix branches
- `release/*`: Release preparation

### Git Workflow

1. Create feature branch from `develop`
2. Implement with atomic commits
3. Open PR against `develop`
4. Pass CI checks (lint, type, test)
5. Code review approval
6. Squash and merge

### Commit Message Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:** feat, fix, docs, style, refactor, test, chore

**Example:**
```
feat(connectors): add HuggingFace dataset download

Implement download functionality for HuggingFace Hub datasets
using the datasets library. Supports streaming for large datasets.

Closes #12
```

---

## Definition of Done

### Story Level

- [ ] Code implements all acceptance criteria
- [ ] Unit tests written (target: 80% coverage)
- [ ] Integration tests for external APIs
- [ ] Code reviewed and approved
- [ ] Documentation updated
- [ ] No regressions in existing tests
- [ ] Changelog entry added

### Sprint Level

- [ ] All committed stories complete
- [ ] Sprint demo conducted
- [ ] No critical bugs open
- [ ] Documentation current
- [ ] Retrospective completed

### Release Level

- [ ] All MVP stories complete
- [ ] E2E tests pass
- [ ] Performance benchmarks met
- [ ] Security review completed
- [ ] User documentation complete
- [ ] Release notes written

---

## Test Strategy

### Test Pyramid

```
        ┌─────────┐
        │   E2E   │  ~10% (end-to-end workflows)
        ├─────────┤
        │ Integr. │  ~20% (API mocking with VCR.py)
        ├─────────┤
        │  Unit   │  ~70% (isolated functions)
        └─────────┘
```

### Unit Tests

- Test individual functions in isolation
- Mock external dependencies
- Fast execution (<1s per test)
- Cover edge cases and error paths

**Example:**
```python
def test_parse_uri_huggingface():
    connector = HuggingFaceConnector()
    dataset_id, params = connector.parse_uri("hf://stanfordnlp/imdb")
    assert dataset_id == "stanfordnlp/imdb"
    assert params == {}

def test_parse_uri_with_revision():
    connector = HuggingFaceConnector()
    dataset_id, params = connector.parse_uri("hf://owner/dataset@v1.0")
    assert dataset_id == "owner/dataset"
    assert params["revision"] == "v1.0"
```

### Integration Tests (VCR.py)

- Record and replay HTTP interactions
- Test connector behavior with real API responses
- Update cassettes periodically

**Example:**
```python
@pytest.mark.vcr()
def test_search_huggingface():
    connector = HuggingFaceConnector()
    results = connector.search("sentiment")
    assert len(results) > 0
    assert all(r.source == "huggingface" for r in results)
```

### End-to-End Tests

- Test complete workflows
- Use small fixture datasets
- Run in CI on every PR

**Example:**
```python
def test_full_build_workflow(tmp_path):
    # Pull, normalize, validate, split, export
    result = runner.invoke(app, [
        "build", "hf://fixture/tiny-dataset",
        "--output", str(tmp_path / "output"),
        "--format", "parquet",
        "--split", "0.8,0.1,0.1"
    ])

    assert result.exit_code == 0
    assert (tmp_path / "output" / "manifest.yaml").exists()
    assert (tmp_path / "output" / "splits" / "train.parquet").exists()
```

### Test Fixtures

Store small test datasets in `fixtures/`:
```
fixtures/
├── tiny-tabular/
│   └── data.csv (100 rows)
├── tiny-text/
│   └── data.jsonl (50 rows)
└── tiny-images/
    ├── metadata.csv
    └── images/ (10 images)
```

---

## Code Review Process

### Review Checklist

**Functionality:**
- [ ] Implements acceptance criteria correctly
- [ ] Handles edge cases appropriately
- [ ] No obvious bugs

**Code Quality:**
- [ ] Follows project style guide
- [ ] Clear, self-documenting code
- [ ] No unnecessary complexity
- [ ] DRY (no duplicated logic)

**Testing:**
- [ ] Tests cover main paths
- [ ] Tests cover error cases
- [ ] Tests are readable and maintainable

**Security:**
- [ ] No hardcoded secrets
- [ ] Input validation present
- [ ] No injection vulnerabilities

**Performance:**
- [ ] No obvious performance issues
- [ ] Large data handled with streaming
- [ ] Appropriate use of lazy evaluation

### Review Process

1. Author creates PR with description
2. CI checks run automatically
3. Reviewer assigned automatically or manually
4. Reviewer provides feedback
5. Author addresses feedback
6. Reviewer approves
7. Author squash-merges

### Approval Requirements

- 1 approval required for features
- 2 approvals for architectural changes
- All CI checks must pass
- No unresolved comments

---

## CI/CD Pipeline

### Pipeline Stages

```
┌─────────────┐   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐
│    Lint     │ → │    Type     │ → │    Test     │ → │   Build     │
│  (ruff)     │   │   (mypy)    │   │  (pytest)   │   │ (package)   │
└─────────────┘   └─────────────┘   └─────────────┘   └─────────────┘
                                           │
                                           ▼
                                    ┌─────────────┐
                                    │  Coverage   │
                                    │  (codecov)  │
                                    └─────────────┘
```

### Release Pipeline

```
tag v0.1.0 → Build → Test → Publish to PyPI → GitHub Release
```

---

## Performance Benchmarks

### Targets

| Operation | Dataset Size | Target Time |
|-----------|--------------|-------------|
| Search | - | < 3s |
| Pull (cached) | 100MB | < 5s |
| Pull (fresh) | 100MB | Network-bound |
| Build (full) | 100MB | < 60s |
| Validate | 100MB | < 30s |
| Split | 100MB | < 10s |
| Export | 100MB | < 20s |

### Benchmark Suite

Create benchmarks in `benchmarks/`:
```python
def benchmark_build_medium_dataset():
    """Benchmark full build on 100MB dataset."""
    with timer() as t:
        build("hf://benchmark/medium", output="./output")

    assert t.elapsed < 60, f"Build took {t.elapsed}s, target <60s"
```

Run benchmarks weekly in CI to catch regressions.

---

## Traceability

| Document | Traces From | Traces To |
|----------|-------------|-----------|
| Implementation Plan | Sprint Backlog | Code, Tests |
| Phase Deliverables | User Stories | Releases |
| Test Strategy | Acceptance Criteria | Test Cases |

---

**End of Document**
