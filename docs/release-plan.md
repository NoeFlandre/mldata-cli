# mldata-cli — Release Plan

## Document Control

| Field | Value |
|-------|-------|
| **Version** | 1.0 |
| **Date** | 2026-01-29 |
| **Author** | Noé Flandre |
| **Status** | Draft |
| **Parent Document** | [Implementation Plan](./implementation-plan.md) |

---

## Release Strategy

### Versioning Scheme

**Semantic Versioning (SemVer):** `MAJOR.MINOR.PATCH`

| Version | Meaning | Example |
|---------|---------|---------|
| `0.x.y` | Pre-1.0 development, breaking changes possible | `0.1.0`, `0.2.0` |
| `1.0.0` | First stable release, public API committed | Production ready |
| `x.y.0` | Minor release with new features, backward compatible | `1.1.0` |
| `x.y.z` | Patch release with bug fixes only | `1.0.1` |

### Release Types

| Type | Version Pattern | Description | Audience |
|------|-----------------|-------------|----------|
| **Alpha** | `0.1.0-alpha.N` | Early development, incomplete features | Internal testers |
| **Beta** | `0.1.0-beta.N` | Feature complete, stabilization phase | Early adopters |
| **RC** | `0.1.0-rc.N` | Release candidate, final testing | Broader testing |
| **GA** | `0.1.0` | General availability, stable release | All users |

### Release Cadence

| Phase | Cadence | Notes |
|-------|---------|-------|
| Alpha | As needed | Frequent updates during development |
| Beta | Bi-weekly | Stabilization period |
| Stable | Monthly | Regular feature releases |
| Patch | As needed | Critical bug fixes |

---

## Release Roadmap

### v0.1.0 — MVP (Target: Sprint 6 completion)

**Theme:** Core dataset pipeline

**Features:**
- Dataset discovery (search, info)
- Download from HuggingFace, Kaggle, OpenML
- Content-addressed caching
- Format conversion (CSV, JSON, Parquet)
- Quality validation (duplicates, labels, missing)
- Train/val/test splitting
- Manifest generation
- Rebuild from manifest

**Milestones:**
| Milestone | Target | Status |
|-----------|--------|--------|
| Alpha 1 | Sprint 2 | Pending |
| Alpha 2 | Sprint 4 | Pending |
| Beta 1 | Sprint 5 | Pending |
| RC 1 | Sprint 6 | Pending |
| GA | Sprint 6 + 1 week | Pending |

---

### v0.2.0 — Enhanced Quality & Versioning

**Theme:** Production readiness

**Features:**
- File integrity checks (images, audio)
- DVC integration
- Git-LFS integration
- Dataset diff command
- Multi-format export
- Framework-specific exports
- Advanced duplicate detection (LSH)

---

### v0.3.0 — Extensibility

**Theme:** Plugin ecosystem

**Features:**
- Plugin architecture for connectors
- Custom check plugins
- Configuration profiles
- S3/GCS connector
- Streaming large datasets
- Parallel downloads

---

### v1.0.0 — Stable Release

**Theme:** Production stability

**Features:**
- API stability guarantee
- Comprehensive documentation
- Performance optimizations
- Enterprise features (optional)
- Wide platform support

---

## Release Process

### Pre-Release Checklist

#### Code Readiness

- [ ] All planned features implemented
- [ ] All tests passing on CI
- [ ] No known critical bugs
- [ ] Code coverage ≥ 80%
- [ ] Type checking passes
- [ ] Linting passes

#### Documentation Readiness

- [ ] README.md updated
- [ ] CLI help text complete
- [ ] User guide complete
- [ ] API documentation generated
- [ ] CHANGELOG.md updated
- [ ] Migration guide (if breaking changes)

#### Quality Assurance

- [ ] Manual testing on Linux
- [ ] Manual testing on macOS
- [ ] Manual testing on Windows (if supported)
- [ ] Performance benchmarks pass
- [ ] Security review completed

#### Release Artifacts

- [ ] Version number updated
- [ ] Dependencies locked (uv.lock)
- [ ] License file present
- [ ] PyPI metadata correct

---

### Release Workflow

```
1. Create Release Branch
   └── git checkout -b release/v0.1.0 develop

2. Version Bump
   └── Update version in pyproject.toml
   └── Update CHANGELOG.md

3. Final Testing
   └── Run full test suite
   └── Manual smoke tests

4. Create Release PR
   └── PR: release/v0.1.0 → main
   └── Review and approve

5. Merge and Tag
   └── Merge to main
   └── git tag v0.1.0
   └── git push --tags

6. Automated Publishing
   └── GitHub Actions builds package
   └── Publishes to PyPI
   └── Creates GitHub Release

7. Post-Release
   └── Merge main back to develop
   └── Announce release
   └── Monitor for issues
```

### GitHub Actions Release Workflow

**.github/workflows/release.yml:**
```yaml
name: Release

on:
  push:
    tags:
      - 'v*'

permissions:
  contents: write

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install uv
        uses: astral-sh/setup-uv@v1

      - name: Build package
        run: uv build

      - name: Upload artifacts
        uses: actions/upload-artifact@v3
        with:
          name: dist
          path: dist/

  test:
    needs: build
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, macos-latest, windows-latest]
        python-version: ["3.9", "3.10", "3.11", "3.12"]
    steps:
      - uses: actions/checkout@v4
      - name: Install uv
        uses: astral-sh/setup-uv@v1
      - name: Run tests
        run: uv run pytest

  publish-pypi:
    needs: test
    runs-on: ubuntu-latest
    environment: pypi
    steps:
      - uses: actions/download-artifact@v3
        with:
          name: dist
          path: dist/

      - name: Publish to PyPI
        uses: pypa/gh-action-pypi-publish@release/v1
        with:
          password: ${{ secrets.PYPI_API_TOKEN }}

  github-release:
    needs: publish-pypi
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/download-artifact@v3
        with:
          name: dist
          path: dist/

      - name: Create GitHub Release
        uses: softprops/action-gh-release@v1
        with:
          files: dist/*
          generate_release_notes: true
          draft: false
```

---

## Distribution Channels

### Primary: PyPI

**Package Name:** `mldata-cli`

**Installation:**
```bash
pip install mldata-cli
# or
uv pip install mldata-cli
# or
pipx install mldata-cli
```

**PyPI Metadata:**
- Homepage: GitHub repo
- Documentation: ReadTheDocs (future)
- Keywords: machine-learning, datasets, cli, ml, data

### GitHub Releases

- Source archives (tar.gz, zip)
- Pre-built wheels
- Changelog excerpt
- Installation instructions

### Future Channels

| Channel | Priority | Notes |
|---------|----------|-------|
| Homebrew | Medium | macOS users prefer |
| conda-forge | Medium | Scientific Python community |
| Docker | Low | Containerized workflows |
| Snap/Flatpak | Low | Linux desktop users |

#### Homebrew Formula (Future)

```ruby
class MldataCli < Formula
  desc "Unified CLI for ML dataset acquisition and preparation"
  homepage "https://github.com/user/mldata-cli"
  url "https://github.com/user/mldata-cli/archive/v0.1.0.tar.gz"
  sha256 "abc123..."
  license "MIT"

  depends_on "python@3.11"

  def install
    virtualenv_install_with_resources
  end

  test do
    system "#{bin}/mldata", "--version"
  end
end
```

---

## Release Notes Template

```markdown
# mldata-cli v0.1.0

**Release Date:** 2026-XX-XX

## Highlights

- First public release of mldata-cli
- Unified dataset CLI for HuggingFace, Kaggle, and OpenML
- Reproducible dataset builds with manifests

## New Features

### Dataset Discovery
- `mldata search` - Search across all sources
- `mldata info` - View detailed dataset metadata

### Dataset Download
- `mldata pull` - Download datasets by URI
- Content-addressed caching
- Resume interrupted downloads

### Data Pipeline
- `mldata build` - Full pipeline execution
- Format conversion (CSV, JSON, Parquet)
- Quality validation with reports
- Deterministic train/val/test splitting

### Reproducibility
- `mldata rebuild` - Rebuild from manifest
- SHA-256 artifact verification
- Full provenance tracking

## Bug Fixes

- None (first release)

## Breaking Changes

- None (first release)

## Deprecations

- None (first release)

## Known Issues

- Windows support is experimental
- Large dataset (>10GB) performance not optimized

## Installation

```bash
pip install mldata-cli
```

## Documentation

- [Getting Started](link)
- [CLI Reference](link)
- [User Guide](link)

## Contributors

- @author - Lead developer

---

**Full Changelog:** https://github.com/user/mldata-cli/compare/...v0.1.0
```

---

## Rollback Plan

### Rollback Triggers

| Trigger | Severity | Action |
|---------|----------|--------|
| Critical bug affecting all users | P0 | Immediate rollback |
| Data corruption risk | P0 | Immediate rollback |
| Security vulnerability | P0 | Immediate rollback |
| Major feature broken | P1 | Rollback within 24h |
| Minor regression | P2 | Patch release |

### Rollback Procedure

1. **Identify Issue**
   - Confirm the issue is release-related
   - Assess impact scope
   - Document the problem

2. **Communicate**
   - Post GitHub issue with "critical" label
   - Notify via social channels if applicable
   - Update status page (if exists)

3. **Execute Rollback**
   ```bash
   # Yank the broken version from PyPI
   # (This hides it but doesn't delete)
   # Requires PyPI maintainer access

   # If previous version is safe:
   # Users can downgrade
   pip install mldata-cli==0.0.9
   ```

4. **Fix Forward**
   - Diagnose root cause
   - Implement fix
   - Release patch version (e.g., v0.1.1)

5. **Post-Mortem**
   - Document what happened
   - Identify process improvements
   - Update test coverage

### User Communication Template

```markdown
## Important: mldata-cli v0.1.0 Rollback Notice

**Date:** 2026-XX-XX

We have identified a critical issue in mldata-cli v0.1.0 that
[brief description of issue].

### Immediate Action Required

If you have installed v0.1.0, please downgrade to the previous
stable version:

```bash
pip install mldata-cli==0.0.9
```

### What Happened

[Detailed explanation]

### Resolution Timeline

We are working on a fix and expect to release v0.1.1 within
[timeframe].

### Affected Users

[Description of who is affected]

### Questions

Please open an issue on GitHub or reach out via [channel].

We apologize for any inconvenience caused.
```

---

## Release Metrics

### Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Install success rate | > 95% | PyPI download vs error logs |
| Critical bugs in first 7 days | 0 | GitHub issues |
| User satisfaction | > 4.0/5 | Survey/feedback |
| Documentation completeness | 100% | Checklist |

### Monitoring Post-Release

1. **First 24 hours**
   - Monitor GitHub issues closely
   - Check PyPI download stats
   - Monitor social mentions

2. **First week**
   - Triage all new issues
   - Release patch if needed
   - Gather user feedback

3. **First month**
   - Analyze usage patterns
   - Plan improvements
   - Update roadmap

---

## Traceability

| Document | Traces From | Traces To |
|----------|-------------|-----------|
| Release Plan | Implementation Plan | PyPI, GitHub Releases |
| Version | Roadmap | Changelog |
| Release Notes | Completed Stories | User Communication |

---

**End of Document**
