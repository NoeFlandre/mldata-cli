# mldata-cli — Sprint Backlog

## Document Control

| Field | Value |
|-------|-------|
| **Version** | 1.0 |
| **Date** | 2026-01-29 |
| **Author** | Noé Flandre |
| **Status** | Draft |
| **Parent Document** | [Prioritized Backlog](./prioritized-backlog.md) |

---

## Sprint 1: Foundation

### Sprint Goal
Establish CLI foundation and enable basic dataset downloads with authentication.

### Sprint Duration
2 weeks (10 working days)

### Sprint Commitment

| Story | Points | Owner | Status | Notes |
|-------|--------|-------|--------|-------|
| **Setup**: Project scaffolding | S (2) | - | Pending | pyproject.toml, structure |
| **US-005**: Download Dataset by URI | M (5) | - | Pending | Core download functionality |
| **US-008**: Authentication Management | M (5) | - | Pending | Keyring + env vars |

**Total Committed:** 12 points

### Sprint 1 Task Breakdown

#### Setup: Project Scaffolding (S)

| Task | Estimate | Status |
|------|----------|--------|
| Initialize uv project with pyproject.toml | 2h | Pending |
| Create directory structure (src/mldata/...) | 1h | Pending |
| Configure pre-commit hooks (ruff, mypy) | 2h | Pending |
| Set up GitHub Actions CI | 2h | Pending |
| Create initial test fixtures | 1h | Pending |
| Write development README | 1h | Pending |

**Task Total:** ~9h

#### US-005: Download Dataset by URI (M)

| Task | Estimate | Status |
|------|----------|--------|
| Design connector base class | 2h | Pending |
| Implement URI parsing (hf://, kaggle://, openml://) | 2h | Pending |
| Implement HuggingFace connector (download) | 4h | Pending |
| Implement Kaggle connector (download) | 4h | Pending |
| Implement OpenML connector (download) | 3h | Pending |
| Create CLI `pull` command with Typer | 2h | Pending |
| Add basic progress reporting (Rich) | 2h | Pending |
| Write unit tests | 3h | Pending |
| Write integration tests (VCR.py) | 3h | Pending |

**Task Total:** ~25h

#### US-008: Authentication Management (M)

| Task | Estimate | Status |
|------|----------|--------|
| Design auth module structure | 1h | Pending |
| Implement keyring storage wrapper | 3h | Pending |
| Implement env var fallback | 1h | Pending |
| Implement config file fallback | 2h | Pending |
| Create `auth login` command | 2h | Pending |
| Create `auth logout` command | 1h | Pending |
| Create `auth status` command | 2h | Pending |
| Implement secret redaction in logs | 2h | Pending |
| Write tests | 3h | Pending |

**Task Total:** ~17h

### Sprint 1 Acceptance Criteria

**Definition of Done for Sprint 1:**
- [ ] Project structure created and documented
- [ ] CI pipeline running on every PR
- [ ] `mldata pull hf://dataset` downloads to local directory
- [ ] `mldata pull kaggle://dataset` downloads to local directory
- [ ] `mldata pull openml://dataset` downloads to local directory
- [ ] `mldata auth login <source>` stores credentials securely
- [ ] `mldata auth status` shows configured sources
- [ ] Credentials never appear in logs or output
- [ ] 80% test coverage for new code
- [ ] All tests pass on Linux and macOS

### Sprint 1 Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Kaggle API complexity | Medium | Medium | Start with simple downloads, expand later |
| Keyring cross-platform issues | Medium | High | Test early on all platforms, have fallback |
| API rate limits during testing | Low | Medium | Use VCR.py for recorded responses |

---

## Sprint 2: Discovery & Caching

### Sprint Goal
Enable dataset discovery with unified search and implement intelligent caching.

### Sprint Commitment

| Story | Points | Owner | Status | Notes |
|-------|--------|-------|--------|-------|
| **US-001**: Unified Dataset Search | L (8) | - | Pending | Search across all sources |
| **US-003**: Dataset Information Display | M (5) | - | Pending | Detailed metadata view |
| **US-006**: Caching Downloaded Data | M (5) | - | Pending | Content-addressed cache |
| **US-009**: Download Progress Reporting | S (2) | - | Pending | Rich progress bars |
| **US-011**: Automatic Format Detection | M (3) | - | Pending | Detect CSV/JSON/Parquet |

**Total Committed:** 23 points

### Sprint 2 Task Breakdown

#### US-001: Unified Dataset Search (L)

| Task | Estimate | Status |
|------|----------|--------|
| Design search result model | 1h | Pending |
| Implement HF search adapter | 3h | Pending |
| Implement Kaggle search adapter | 3h | Pending |
| Implement OpenML search adapter | 3h | Pending |
| Create result aggregation/ranking | 3h | Pending |
| Create CLI `search` command | 2h | Pending |
| Implement Rich table output | 2h | Pending |
| Write tests | 4h | Pending |

**Task Total:** ~21h

#### US-003: Dataset Information Display (M)

| Task | Estimate | Status |
|------|----------|--------|
| Design metadata model | 1h | Pending |
| Implement metadata fetching per connector | 4h | Pending |
| Create CLI `info` command | 2h | Pending |
| Implement Rich panel display | 2h | Pending |
| Add schema display | 2h | Pending |
| Write tests | 2h | Pending |

**Task Total:** ~13h

#### US-006: Caching Downloaded Data (M)

| Task | Estimate | Status |
|------|----------|--------|
| Design cache module structure | 2h | Pending |
| Implement content-addressed storage | 3h | Pending |
| Implement cache key generation (SHA-256) | 1h | Pending |
| Implement LRU eviction | 2h | Pending |
| Add cache hit/miss logging | 1h | Pending |
| Integrate with pull command | 2h | Pending |
| Write tests | 3h | Pending |

**Task Total:** ~14h

#### US-009: Download Progress Reporting (S)

| Task | Estimate | Status |
|------|----------|--------|
| Implement Rich progress bars | 2h | Pending |
| Add ETA calculation | 1h | Pending |
| Handle unknown file sizes | 1h | Pending |
| Write tests | 1h | Pending |

**Task Total:** ~5h

#### US-011: Automatic Format Detection (M)

| Task | Estimate | Status |
|------|----------|--------|
| Implement extension-based detection | 1h | Pending |
| Implement content sniffing | 2h | Pending |
| Support CSV, JSON, JSONL, Parquet | 2h | Pending |
| Add detection to pull pipeline | 1h | Pending |
| Write tests | 2h | Pending |

**Task Total:** ~8h

### Sprint 2 Acceptance Criteria

- [ ] `mldata search <query>` returns results from all sources
- [ ] `mldata info <uri>` shows comprehensive metadata
- [ ] Second `pull` of same dataset uses cache (no network)
- [ ] Progress bars show during downloads
- [ ] Format detected automatically after download

---

## Sprint 3: Normalization & Splitting

### Sprint Goal
Implement data normalization pipeline and deterministic splitting.

### Sprint Commitment

| Story | Points | Owner | Status | Notes |
|-------|--------|-------|--------|-------|
| **US-012**: Format Conversion | M (5) | - | Pending | CSV/JSON/Parquet conversion |
| **US-013**: Standardized Directory Layout | M (3) | - | Pending | Consistent output structure |
| **US-022**: Basic Train/Val/Test Split | M (5) | - | Pending | Configurable ratios |
| **US-024**: Deterministic Seeding | S (2) | - | Pending | Reproducible splits |
| **US-034**: Manifest Generation | M (5) | - | Pending | Full provenance capture |

**Total Committed:** 20 points

### Sprint 3 Task Breakdown

#### US-012: Format Conversion (M)

| Task | Estimate | Status |
|------|----------|--------|
| Design converter interface | 1h | Pending |
| Implement CSV → Parquet | 2h | Pending |
| Implement JSON/JSONL → Parquet | 2h | Pending |
| Implement Parquet → CSV | 1h | Pending |
| Implement Parquet → JSONL | 1h | Pending |
| Handle type preservation | 2h | Pending |
| Write tests | 3h | Pending |

**Task Total:** ~12h

#### US-013: Standardized Directory Layout (M)

| Task | Estimate | Status |
|------|----------|--------|
| Define layout specification | 1h | Pending |
| Implement directory creator | 2h | Pending |
| Integrate with pull/build commands | 2h | Pending |
| Write tests | 2h | Pending |

**Task Total:** ~7h

#### US-022: Basic Train/Val/Test Split (M)

| Task | Estimate | Status |
|------|----------|--------|
| Design split module | 1h | Pending |
| Implement random splitting | 2h | Pending |
| Implement ratio parsing | 1h | Pending |
| Create CLI `split` command | 2h | Pending |
| Save split files | 2h | Pending |
| Write tests | 3h | Pending |

**Task Total:** ~11h

#### US-024: Deterministic Seeding (S)

| Task | Estimate | Status |
|------|----------|--------|
| Add seed parameter to split | 1h | Pending |
| Ensure reproducibility | 1h | Pending |
| Record seed in manifest | 1h | Pending |
| Write tests | 1h | Pending |

**Task Total:** ~4h

#### US-034: Manifest Generation (M)

| Task | Estimate | Status |
|------|----------|--------|
| Design manifest schema | 2h | Pending |
| Implement manifest builder | 3h | Pending |
| Capture provenance hashes | 2h | Pending |
| Generate on build completion | 2h | Pending |
| Write tests | 3h | Pending |

**Task Total:** ~12h

### Sprint 3 Acceptance Criteria

- [ ] `mldata build --format parquet` converts data correctly
- [ ] Output directory follows standardized layout
- [ ] `mldata split --ratios 0.8,0.1,0.1` creates three splits
- [ ] Same seed produces identical splits
- [ ] manifest.yaml generated with all build parameters

---

## Sprint 4: Validation & Export

### Sprint Goal
Implement quality validation checks and Parquet export with rebuild capability.

### Sprint Commitment

| Story | Points | Owner | Status | Notes |
|-------|--------|-------|--------|-------|
| **US-016**: Duplicate Detection | L (8) | - | Pending | Exact + near duplicates |
| **US-017**: Label Distribution Analysis | M (3) | - | Pending | Class imbalance detection |
| **US-018**: Missing Value Detection | S (2) | - | Pending | Null/NaN detection |
| **US-021**: Quality Report Generation | M (5) | - | Pending | JSON + Markdown reports |
| **US-026**: Parquet Export | M (5) | - | Pending | Efficient columnar export |
| **US-032**: Rebuild from Manifest | L (8) | - | Pending | Reproducible rebuilds |

**Total Committed:** 31 points

### Sprint 4 Task Breakdown

#### US-016: Duplicate Detection (L)

| Task | Estimate | Status |
|------|----------|--------|
| Design check interface | 1h | Pending |
| Implement exact duplicate detection (hash) | 2h | Pending |
| Implement near-duplicate detection | 4h | Pending |
| Add configurable threshold | 1h | Pending |
| Integrate with validate command | 2h | Pending |
| Write tests | 4h | Pending |

**Task Total:** ~14h

#### US-017: Label Distribution Analysis (M)

| Task | Estimate | Status |
|------|----------|--------|
| Implement label counting | 1h | Pending |
| Calculate imbalance metrics | 1h | Pending |
| Add configurable thresholds | 1h | Pending |
| Write tests | 2h | Pending |

**Task Total:** ~5h

#### US-018: Missing Value Detection (S)

| Task | Estimate | Status |
|------|----------|--------|
| Implement null counting | 1h | Pending |
| Calculate missing percentages | 1h | Pending |
| Write tests | 1h | Pending |

**Task Total:** ~3h

#### US-021: Quality Report Generation (M)

| Task | Estimate | Status |
|------|----------|--------|
| Design report schema | 2h | Pending |
| Implement JSON report generator | 2h | Pending |
| Implement Markdown report generator | 2h | Pending |
| Create CLI `validate` command | 2h | Pending |
| Write tests | 3h | Pending |

**Task Total:** ~11h

#### US-026: Parquet Export (M)

| Task | Estimate | Status |
|------|----------|--------|
| Implement Parquet writer | 2h | Pending |
| Add compression options | 2h | Pending |
| Integrate with export command | 2h | Pending |
| Write tests | 2h | Pending |

**Task Total:** ~8h

#### US-032: Rebuild from Manifest (L)

| Task | Estimate | Status |
|------|----------|--------|
| Implement manifest parser | 2h | Pending |
| Create rebuild orchestrator | 4h | Pending |
| Re-fetch from source | 2h | Pending |
| Re-apply all transformations | 3h | Pending |
| Create CLI `rebuild` command | 2h | Pending |
| Write tests | 4h | Pending |

**Task Total:** ~17h

### Sprint 4 Acceptance Criteria

- [ ] `mldata validate` detects duplicates and reports count
- [ ] Label distribution shown with imbalance warning
- [ ] Missing values detected and reported
- [ ] Quality report saved as JSON and Markdown
- [ ] `mldata export --format parquet` produces valid Parquet
- [ ] `mldata rebuild manifest.yaml` recreates dataset

---

## Sprint 5: Polish & Extensions

### Sprint Goal
Add advanced features and polish the user experience.

### Sprint Commitment

| Story | Points | Owner | Status | Notes |
|-------|--------|-------|--------|-------|
| **US-014**: Schema Inference | M (5) | - | Pending | Automatic type detection |
| **US-019**: Schema Validation | M (3) | - | Pending | Cross-split consistency |
| **US-023**: Stratified Splitting | M (5) | - | Pending | Preserve label distribution |
| **US-025**: Split Index Files | S (2) | - | Pending | Exportable indices |
| **US-027**: JSONL Export | S (2) | - | Pending | JSON Lines format |
| **US-033**: Build Verification | M (3) | - | Pending | Hash comparison |

**Total Committed:** 20 points

### Sprint 5 Acceptance Criteria

- [ ] Schema automatically inferred and saved in manifest
- [ ] Schema consistency validated across splits
- [ ] `--stratify` preserves label distribution in splits
- [ ] Split index files generated and exportable
- [ ] JSONL export working alongside Parquet
- [ ] Rebuild verification compares hashes

---

## Sprint 6: Complete MVP

### Sprint Goal
Complete remaining MVP features, fix bugs, and prepare for release.

### Sprint Commitment

| Story | Points | Owner | Status | Notes |
|-------|--------|-------|--------|-------|
| **US-002**: Filter Search Results | M (5) | - | Pending | Source/modality/task filters |
| **US-007**: Resume Interrupted Downloads | M (5) | - | Pending | Resume partial downloads |
| Bug fixes and polish | M (5) | - | Pending | Based on testing |
| Documentation | M (5) | - | Pending | User guide, API docs |

**Total Committed:** 20 points

### Sprint 6 Acceptance Criteria

- [ ] Search filters working (--source, --modality, --task)
- [ ] Interrupted downloads resume correctly
- [ ] All known bugs fixed
- [ ] User documentation complete
- [ ] README ready for release
- [ ] Changelog written

---

## Sprint Metrics Template

Track these metrics each sprint:

| Metric | Sprint 1 | Sprint 2 | Sprint 3 | Sprint 4 | Sprint 5 | Sprint 6 |
|--------|----------|----------|----------|----------|----------|----------|
| Committed Points | 12 | 23 | 20 | 31 | 20 | 20 |
| Completed Points | - | - | - | - | - | - |
| Velocity | - | - | - | - | - | - |
| Bugs Found | - | - | - | - | - | - |
| Bugs Fixed | - | - | - | - | - | - |
| Test Coverage | - | - | - | - | - | - |

---

## Daily Standup Template

```
Date: ____

What I did yesterday:
-

What I'm doing today:
-

Blockers:
-

Notes:
-
```

---

## Sprint Review Template

```
Sprint: ____
Date: ____

Completed Stories:
-

Not Completed:
-

Demo Notes:
-

Stakeholder Feedback:
-

Action Items:
-
```

---

## Sprint Retrospective Template

```
Sprint: ____
Date: ____

What went well:
-

What could improve:
-

Action items for next sprint:
-
```

---

## Traceability

| Document | Traces From | Traces To |
|----------|-------------|-----------|
| Sprint Backlog | Prioritized Backlog | Implementation |
| Sprint Tasks | User Stories | Code, Tests |
| Acceptance Criteria | Story AC | Test Cases |

---

**End of Document**
