# Changelog

All notable changes to mldata-cli will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.4.0] - 2025-01-29

### Added

- **Download Resume**: Interrupted downloads automatically resume from partial files
- **File Integrity Checks**: Validate image and audio file integrity
- **DVC Integration**: Generate .dvc files for dataset versioning with DVC
- **Git-LFS Integration**: Configure Git-LFS tracking for large files
- **Multi-Format Export**: Export to multiple formats simultaneously
- **Framework Templates**: Export with PyTorch, TensorFlow, and JAX loader code
- **Incremental Builds**: Skip reprocessing unchanged files with SHA-256 hashing

### Features

- Partial download detection and state persistence
- Range request support for resuming downloads
- ETA calculation and speed display during downloads
- Image validation (JPEG, PNG, GIF, WebP, etc.)
- Audio validation (WAV, MP3, FLAC, OGG, etc.)
- Configurable sampling for file integrity checks
- Automatic .dvc file generation with manifest hash integration
- Auto-detect files >10MB for Git-LFS tracking
- Parallel file conversion for multi-format export
- PyTorch Dataset + DataLoader code generation
- TensorFlow Dataset code generation
- JAX numpy arrays export

### Testing

- 91 unit and integration tests
- Test coverage for core functionality
- Tests for DVC, Git-LFS, and framework export services
- Tests for file integrity validation

## [0.1.0] - 2024-01-29

### Added

- **Unified Dataset Interface**: Single CLI for HuggingFace, Kaggle, and OpenML
- **Search Command**: Search datasets across all sources with filters
- **Pull Command**: Download datasets with content-addressed caching
- **Build Command**: Full pipeline (fetch, normalize, validate, split, export)
- **Validate Command**: Quality checks for duplicates, labels, missing values, schema
- **Split Command**: Train/val/test splitting with stratification support
- **Export Command**: Convert between CSV, Parquet, and JSONL formats
- **Rebuild Command**: Reproducible builds from manifest
- **Diff Command**: Compare two dataset builds
- **Auth Command**: Manage credentials for all sources
- **Doctor Command**: Diagnose configuration and connectivity

### Features

- Content-addressed caching with SHA-256 hashes
- Deterministic splitting with configurable seeds
- Stratified splitting to preserve label distribution
- Quality reports in JSON and Markdown formats
- Manifest-based provenance tracking
- Compression support (snappy, gzip, zstd)

### Supported Sources

- HuggingFace Hub (`hf://`)
- Kaggle (`kaggle://`)
- OpenML (`openml://`)
- Local files and directories

### Supported Formats

- CSV
- Parquet
- JSONL

### Testing

- 51 unit and integration tests
- Test coverage for core functionality
- E2E tests for build pipeline

### Documentation

- Complete CLI reference
- Quick start guide
- URI scheme documentation
- Output structure guide
- Configuration documentation

### Code Quality

- Type hints with Pydantic models
- Async/await patterns for I/O operations
- Polars for efficient DataFrame operations
- Ruff and mypy for linting
- Pre-commit hooks
