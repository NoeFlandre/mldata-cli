# mldata-cli — Epic List

## Document Control

| Field | Value |
|-------|-------|
| **Version** | 1.0 |
| **Date** | 2026-01-29 |
| **Author** | Noé Flandre |
| **Status** | Draft |
| **Parent Document** | [PRD](./PRD.md) |

---

## Epic Overview

| ID | Epic | Description | Priority | Stories |
|----|------|-------------|----------|---------|
| E1 | Discovery & Search | Unified dataset search across HF/Kaggle/OpenML | P0 | 4 |
| E2 | Fetch & Download | Multi-source download with caching and resume | P0 | 6 |
| E3 | Normalization | Standardized directory structure and format conversion | P1 | 5 |
| E4 | Quality Validation | Duplicate detection, label analysis, schema validation | P1 | 6 |
| E5 | Splitting | Deterministic train/val/test with stratification | P0 | 4 |
| E6 | Export & Versioning | Parquet/JSONL export, DVC/Git-LFS integration | P1 | 6 |
| E7 | Rebuild & Diff | Manifest-based rebuild, change detection | P0 | 4 |

---

## Epic Details

### E1: Discovery & Search

**Goal:** Enable users to find datasets across multiple sources with a unified search experience.

**Value Proposition:** Users no longer need to visit multiple platforms or learn different query syntaxes. One command searches everywhere.

**Key Capabilities:**
- Unified search across HuggingFace, Kaggle, OpenML
- Consistent filtering by modality, task, size, license
- Rich metadata preview without downloading
- Dataset info command for detailed exploration

**Success Criteria:**
- Search returns relevant results from all configured sources
- Metadata is normalized across sources
- Response time < 3 seconds for typical queries

**Dependencies:** Authentication system (E2)

**Traces To:** PRD FR1, Vision §4.1.1

---

### E2: Fetch & Download

**Goal:** Reliably download datasets from any supported source with caching and resume support.

**Value Proposition:** Users pull datasets with one command regardless of source, with smart caching to avoid redundant downloads.

**Key Capabilities:**
- URI-based dataset identification (`hf://`, `kaggle://`, `openml://`)
- Content-addressed cache using SHA-256
- Resumable downloads for large datasets
- Progress reporting with Rich
- Multi-file dataset support
- Authentication management (keyring, env vars, config)

**Success Criteria:**
- Downloads resume after interruption
- Cache hit avoids network requests
- Progress shows accurate ETA and speed

**Dependencies:** None (foundation epic)

**Traces To:** PRD FR2, FR3, Vision §4.1.2

---

### E3: Normalization

**Goal:** Transform downloaded datasets into a standardized structure and format.

**Value Proposition:** Downstream tools and scripts can rely on consistent layout and formats regardless of source.

**Key Capabilities:**
- Automatic format detection
- Conversion between CSV, JSONL, Parquet
- Standardized directory layout
- Schema inference and documentation
- Handling of multimodal data (images, audio references)

**Success Criteria:**
- All supported formats detected correctly
- Conversion preserves data integrity
- Output layout matches specification

**Dependencies:** E2 (Fetch)

**Traces To:** PRD FR4, FR5, Vision §4.1.3

---

### E4: Quality Validation

**Goal:** Automatically detect data quality issues before training.

**Value Proposition:** Users catch duplicates, label issues, and data problems early—not during training failure.

**Key Capabilities:**
- Exact and near-duplicate detection
- Label distribution analysis
- Missing value detection
- Schema consistency validation
- File integrity checks (images/audio)
- JSON and Markdown quality reports

**Success Criteria:**
- Duplicates detected with configurable threshold
- Label imbalance flagged with actionable thresholds
- Reports generated in both human and machine-readable formats

**Dependencies:** E3 (Normalization)

**Traces To:** PRD FR6, FR7, FR8, Vision §4.1.4

---

### E5: Splitting

**Goal:** Generate deterministic, reproducible train/val/test splits.

**Value Proposition:** Experiments are comparable because splits are reproducible and configurable.

**Key Capabilities:**
- Configurable split ratios
- Deterministic seeding (reproducible splits)
- Stratified splitting for classification
- Split index file generation
- Group-aware splitting (prevent data leakage)

**Success Criteria:**
- Same seed produces identical splits
- Stratification preserves label distribution (within tolerance)
- Split indices exportable for external use

**Dependencies:** E3 (Normalization)

**Traces To:** PRD FR9, FR10, Vision §4.1.5

---

### E6: Export & Versioning

**Goal:** Export datasets in standard formats and integrate with version control systems.

**Value Proposition:** Datasets are ready for any framework and tracked alongside code.

**Key Capabilities:**
- Parquet export (columnar, efficient)
- JSONL export (streaming, human-readable)
- DVC integration (`.dvc` files, remote storage)
- Git-LFS integration (large file tracking)
- Multiple format export in single build
- Framework-specific exports (PyTorch, TensorFlow)

**Success Criteria:**
- Exports match source data exactly
- DVC/Git-LFS integration works with existing repos
- Export formats validated against schemas

**Dependencies:** E3 (Normalization), E5 (Splitting)

**Traces To:** PRD FR11, FR12, Vision §4.1.6

---

### E7: Rebuild & Diff

**Goal:** Enable reproducible rebuilds and change detection between builds.

**Value Proposition:** Teams can recreate exact dataset state and understand what changed.

**Key Capabilities:**
- Manifest generation with full provenance
- Rebuild from manifest file
- Build verification (hash comparison)
- Diff between two manifests/builds
- Change summary (row counts, label distribution changes)

**Success Criteria:**
- Rebuild produces identical hashes when inputs unchanged
- Diff clearly shows additions, deletions, modifications
- Manifest captures all parameters needed for rebuild

**Dependencies:** E2 (Fetch), E3 (Normalization), E5 (Splitting), E6 (Export)

**Traces To:** PRD FR13, FR14, FR15, Vision §4.1.7

---

## End-to-End User Flows

### Flow 1: Quick Dataset Pull

**Persona:** Student / Indie Hacker
**Goal:** Get a dataset ready for experimentation quickly

```
┌─────────────────────────────────────────────────────────────────┐
│  User: "I need a sentiment dataset for my project"              │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  mldata search "sentiment" --modality text --limit 10           │
│  ─────────────────────────────────────────────────────────────  │
│  E1: Discovery returns results from HF, Kaggle, OpenML          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  mldata info hf://stanfordnlp/imdb                              │
│  ─────────────────────────────────────────────────────────────  │
│  E1: Display detailed metadata, license, size                   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  mldata pull hf://stanfordnlp/imdb --format parquet             │
│  ─────────────────────────────────────────────────────────────  │
│  E2: Download with progress                                     │
│  E3: Convert to Parquet                                         │
│  E5: Generate default splits                                    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  Output: ./mldata/imdb/ with train/val/test splits              │
│  User starts training immediately                               │
└─────────────────────────────────────────────────────────────────┘
```

**Epics Involved:** E1, E2, E3, E5

---

### Flow 2: Full Build Pipeline

**Persona:** ML Research Engineer
**Goal:** Create a validated, production-ready dataset

```
┌─────────────────────────────────────────────────────────────────┐
│  User: "I need a clean, validated dataset for my benchmark"     │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  mldata search "image classification" --source kaggle           │
│  ─────────────────────────────────────────────────────────────  │
│  E1: Discover datasets                                          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  mldata build kaggle://mnist --output ./data/mnist              │
│    --validate all                                               │
│    --split 0.8,0.1,0.1                                          │
│    --stratify label                                             │
│    --format parquet                                             │
│  ─────────────────────────────────────────────────────────────  │
│  E2: Fetch dataset                                              │
│  E3: Normalize to standard layout                               │
│  E4: Run all quality checks                                     │
│  E5: Create stratified splits                                   │
│  E6: Export to Parquet                                          │
│  E7: Generate manifest                                          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  Output:                                                        │
│  ./data/mnist/                                                  │
│    manifest.yaml                                                │
│    reports/quality.json, quality.md                             │
│    splits/train.parquet, val.parquet, test.parquet              │
│    artifacts/dataset.parquet                                    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  User reviews quality report, proceeds with training            │
└─────────────────────────────────────────────────────────────────┘
```

**Epics Involved:** E1, E2, E3, E4, E5, E6, E7

---

### Flow 3: Reproducible Rebuild

**Persona:** ML Engineer (startup)
**Goal:** Recreate exact dataset from 3 months ago for debugging

```
┌─────────────────────────────────────────────────────────────────┐
│  User: "I need to reproduce the dataset from experiment #42"    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  # Locate manifest from experiment                              │
│  git show exp-42:data/mnist/manifest.yaml > manifest.yaml       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  mldata rebuild manifest.yaml --output ./data/mnist-rebuild     │
│  ─────────────────────────────────────────────────────────────  │
│  E7: Parse manifest, extract parameters                         │
│  E2: Fetch from cache or source                                 │
│  E3: Apply same normalization                                   │
│  E5: Recreate identical splits (same seed)                      │
│  E6: Export in same format                                      │
│  E7: Verify hashes match                                        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  mldata diff manifest.yaml ./data/mnist-rebuild/manifest.yaml   │
│  ─────────────────────────────────────────────────────────────  │
│  E7: Compare manifests, report any differences                  │
│  Output: "Builds are identical" or detailed diff                │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  User has exact dataset state, can debug with confidence        │
└─────────────────────────────────────────────────────────────────┘
```

**Epics Involved:** E2, E3, E5, E6, E7

---

### Flow 4: CI Integration

**Persona:** ML Engineer (startup)
**Goal:** Automate dataset builds in CI pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│  # .github/workflows/dataset.yml                                │
│  # Triggered on: push to main, weekly schedule                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  mldata auth status --json                                      │
│  ─────────────────────────────────────────────────────────────  │
│  E2: Verify credentials configured (exit 0 or 4)                │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  mldata build hf://company/dataset                              │
│    --config mldata.yaml                                         │
│    --json                                                       │
│  ─────────────────────────────────────────────────────────────  │
│  E2-E7: Full pipeline with JSON output                          │
│  Exit codes: 0=success, 1=build fail, 2=validation issues       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  # Parse JSON output, fail on validation errors                 │
│  if [ $? -eq 2 ]; then                                          │
│    echo "Quality issues found, see report"                      │
│    exit 1                                                       │
│  fi                                                             │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  dvc add data/dataset                                           │
│  git add data/dataset.dvc data/dataset/manifest.yaml            │
│  git commit -m "Update dataset build"                           │
│  ─────────────────────────────────────────────────────────────  │
│  E6: Version with DVC, commit manifest                          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  Dataset versioned, reproducible, quality-gated                 │
└─────────────────────────────────────────────────────────────────┘
```

**Epics Involved:** E2, E3, E4, E5, E6, E7

---

## Epic Dependencies

```
                    ┌─────────────┐
                    │ E1 Discovery│
                    └──────┬──────┘
                           │ (auth)
                           ▼
                    ┌─────────────┐
          ┌─────────│  E2 Fetch   │─────────┐
          │         └──────┬──────┘         │
          │                │                │
          ▼                ▼                ▼
   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
   │E3 Normalize │  │             │  │             │
   └──────┬──────┘  │             │  │             │
          │         │             │  │             │
          ├─────────┼─────────────┤  │             │
          │         │             │  │             │
          ▼         ▼             │  │             │
   ┌─────────────┐  ┌─────────────┐  │             │
   │ E4 Validate │  │  E5 Split   │  │             │
   └──────┬──────┘  └──────┬──────┘  │             │
          │                │         │             │
          └────────┬───────┘         │             │
                   │                 │             │
                   ▼                 │             │
            ┌─────────────┐          │             │
            │  E6 Export  │◄─────────┘             │
            └──────┬──────┘                        │
                   │                               │
                   ▼                               │
            ┌─────────────┐                        │
            │ E7 Rebuild  │◄───────────────────────┘
            └─────────────┘
```

---

## Traceability Matrix

| Epic | PRD Requirements | Vision Sections | Stories |
|------|------------------|-----------------|---------|
| E1 | FR1 | §4.1.1 | US-001 to US-004 |
| E2 | FR2, FR3 | §4.1.2 | US-005 to US-010 |
| E3 | FR4, FR5 | §4.1.3 | US-011 to US-015 |
| E4 | FR6, FR7, FR8 | §4.1.4 | US-016 to US-021 |
| E5 | FR9, FR10 | §4.1.5 | US-022 to US-025 |
| E6 | FR11, FR12 | §4.1.6 | US-026 to US-031 |
| E7 | FR13, FR14, FR15 | §4.1.7 | US-032 to US-035 |

---

**End of Document**
