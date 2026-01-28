# mldata-cli — Product Requirements Document (PRD)

## Document Control

| Field | Value |
|-------|-------|
| **Version** | 1.0 |
| **Date** | 2026-01-29 |
| **Author** | Noé Flandre |
| **Status** | Draft |
| **Parent Document** | [Product Vision](./product-vision.md) |

---

## Executive Summary

mldata-cli is a unified, reproducible dataset CLI that standardizes the dataset lifecycle across popular ML dataset ecosystems. It transforms the fragmented experience of "find a dataset and make it train-ready" into a single, coherent workflow: **Discover → Fetch → Normalize → Validate → Split → Export → Version → Rebuild**.

The tool addresses critical pain points in ML development: source fragmentation across platforms (Hugging Face, Kaggle, OpenML), non-reproducible dataset builds, late discovery of data quality issues, and brittle preprocessing pipelines. mldata-cli aims to become the dataset equivalent of `git clone` + `make`—a single interface that reliably converts a dataset reference into a versioned, validated, train/val/test artifact.

---

## Goals & Non-Goals

### Goals

| ID | Goal | Success Indicator |
|----|------|-------------------|
| G1 | **Unified CLI for multi-source datasets** | Users access HF, Kaggle, OpenML with identical commands |
| G2 | **Reproducible builds** | Same manifest + inputs = identical artifact hashes |
| G3 | **Quality-first by default** | Every build includes validation and quality reports |
| G4 | **CI-friendly operation** | Deterministic outputs, structured logs, exit codes for automation |
| G5 | **Fast time-to-train-ready** | Median < 60s for cached medium datasets |

### Non-Goals

| ID | Non-Goal | Rationale |
|----|----------|-----------|
| NG1 | End-to-end model training orchestration | Leave to training frameworks (PyTorch Lightning, etc.) |
| NG2 | Full ETL/warehouse workflows | Out of scope; dbt/Spark handle large-scale transforms |
| NG3 | Labeling and annotation platforms | Specialized tools exist (Label Studio, etc.) |
| NG4 | Enterprise governance features | Phase 2+ concern (identity, policy, approvals) |
| NG5 | Sensitive/regulated data compliance | Beyond basic controls; enterprise feature |

---

## User Personas

### Persona 1: ML Research Engineer

**Profile:**
- Works at research lab or university
- Builds benchmark suites across multiple datasets and sources
- Publishes papers requiring reproducible experiments

**Goals:**
- Quickly discover and pull datasets from various sources
- Create reproducible dataset snapshots tied to experiments
- Run quality checks to ensure benchmark validity

**Pain Points:**
- Each platform has different APIs and authentication
- Reproducing dataset state from 6 months ago is difficult
- Manual quality checks are time-consuming

**Key Jobs-to-be-Done:**
- JTBD-1: Get a dataset fast, correctly
- JTBD-4: Rebuild the exact same dataset later

---

### Persona 2: ML Engineer (Startup/Scale-up)

**Profile:**
- Works at growth-stage company with ML products
- Responsible for production ML pipelines and CI/CD
- Values automation, determinism, and integration with existing tools

**Goals:**
- Automate dataset preparation in CI pipelines
- Version datasets alongside model releases
- Ensure consistent data across team members

**Pain Points:**
- Dataset builds break due to upstream changes
- Team members have different local dataset states
- No clear audit trail for dataset versions

**Key Jobs-to-be-Done:**
- JTBD-2: Make it train-ready and comparable
- JTBD-4: Rebuild the exact same dataset later

---

### Persona 3: Data Scientist Transitioning to Production

**Profile:**
- Moving from notebook-based exploration to production ML
- Wants "one command" solutions without deep tooling expertise
- Needs guardrails to catch common issues

**Goals:**
- Simple commands that "just work"
- Automatic detection of data quality issues
- Standard output formats for downstream frameworks

**Pain Points:**
- Overwhelmed by tool choices (DVC, Great Expectations, etc.)
- Quality issues discovered late during training
- Inconsistent preprocessing across projects

**Key Jobs-to-be-Done:**
- JTBD-1: Get a dataset fast, correctly
- JTBD-3: Trust the data

---

### Persona 4: Student / Indie Hacker

**Profile:**
- Learning ML or building side projects
- Limited time and infrastructure budget
- Prioritizes speed and simplicity

**Goals:**
- Minimal setup and configuration
- Fast access to popular datasets
- Easy exports for common frameworks (PyTorch, TensorFlow)

**Pain Points:**
- Authentication setup is confusing
- Too many tools to learn
- Documentation is scattered across platforms

**Key Jobs-to-be-Done:**
- JTBD-1: Get a dataset fast, correctly

---

## High-Level Requirements

### Functional Requirements

| ID | Requirement | Priority | Traces To |
|----|-------------|----------|-----------|
| FR1 | Search datasets across HF, Kaggle, OpenML with unified query syntax | P0 | E1, Vision §4.1.1 |
| FR2 | Pull datasets by URI with automatic source detection | P0 | E2, Vision §4.1.2 |
| FR3 | Cache downloads with content-addressed storage | P0 | E2, Vision §4.1.2 |
| FR4 | Normalize datasets to standardized directory layout | P1 | E3, Vision §4.1.3 |
| FR5 | Convert between formats (CSV, JSONL, Parquet) | P1 | E3, Vision §4.1.3 |
| FR6 | Detect duplicate samples using configurable strategies | P1 | E4, Vision §4.1.4 |
| FR7 | Analyze label distributions and class imbalance | P1 | E4, Vision §4.1.4 |
| FR8 | Validate schema consistency across splits | P1 | E4, Vision §4.1.4 |
| FR9 | Generate deterministic train/val/test splits | P0 | E5, Vision §4.1.5 |
| FR10 | Support stratified splitting for classification tasks | P1 | E5, Vision §4.1.5 |
| FR11 | Export to Parquet and JSONL formats | P0 | E6, Vision §4.1.6 |
| FR12 | Integrate with DVC for dataset versioning | P1 | E6, Vision §4.1.6 |
| FR13 | Generate manifest files capturing full build provenance | P0 | E7, Vision §4.1.7 |
| FR14 | Rebuild datasets from manifest files | P0 | E7, Vision §4.1.7 |
| FR15 | Diff two dataset builds showing changes | P2 | E7, Vision §4.1.7 |

### Non-Functional Requirements

| ID | Requirement | Target | Priority |
|----|-------------|--------|----------|
| NFR1 | Build time for cached medium dataset | < 60 seconds | P0 |
| NFR2 | CLI startup time | < 500ms | P1 |
| NFR3 | Memory usage for 1GB dataset | < 2GB peak | P1 |
| NFR4 | Python version support | 3.9+ | P0 |
| NFR5 | Cross-platform support | Linux, macOS, Windows | P0 |
| NFR6 | Offline operation after initial download | Full functionality | P1 |

---

## Scope

### In Scope (MVP)

1. **Discovery**
   - Unified search across HuggingFace, Kaggle, OpenML
   - Metadata preview (size, schema, modalities, licenses)
   - Dataset info command with detailed view

2. **Fetch & Download**
   - Pull by URI (`hf://`, `kaggle://`, `openml://`)
   - Content-addressed caching with SHA-256
   - Resume interrupted downloads
   - Progress reporting with Rich

3. **Normalize & Preprocess**
   - Standardized directory layout
   - Format detection and conversion
   - Schema inference and validation

4. **Quality Checks**
   - Duplicate detection (exact and near-duplicate)
   - Label distribution analysis
   - Missing value detection
   - File integrity checks (images/audio)
   - JSON and Markdown quality reports

5. **Splitting**
   - Configurable train/val/test ratios
   - Deterministic seeding
   - Stratification support
   - Split index files

6. **Export & Versioning**
   - Parquet and JSONL export
   - DVC integration
   - Git-LFS integration
   - Manifest generation

7. **Rebuild & Diff**
   - Manifest-based rebuild
   - Build verification
   - Change detection

### Out of Scope (MVP)

- Additional connectors (S3, GCS, Azure, UCI)
- Custom transformation plugins
- Distributed processing
- Web UI / dashboard
- Team collaboration features
- Enterprise SSO / RBAC

---

## Assumptions & Constraints

### Assumptions

| ID | Assumption | Risk if Invalid |
|----|------------|-----------------|
| A1 | Users want unified interface across sources | Core value prop fails |
| A2 | Strong defaults beat flexibility-first design | Adoption friction |
| A3 | Fast, lightweight quality checks will be adopted | Quality features unused |
| A4 | Python is acceptable as runtime | Limits some users |
| A5 | CLI-first is preferred over GUI for target users | Adoption limited |

### Constraints

| ID | Constraint | Impact |
|----|------------|--------|
| C1 | Package manager: `uv` (not Poetry) | Build tooling choice |
| C2 | Python 3.9+ minimum | Excludes older environments |
| C3 | Rate limits on external APIs | Caching critical |
| C4 | Dataset licenses vary widely | Compliance messaging required |
| C5 | Large datasets may exceed local storage | Streaming/partial download needed |

---

## Success Metrics (KPIs)

### North Star Metric

**Time-to-Train-Ready Dataset (TTRD)**
- **Definition:** Median elapsed time from initiating build to producing train-ready artifact
- **Target:** < 60 seconds (cached), source-dependent (fresh download)
- **Measurement:** CLI telemetry (opt-in) tracking `build_start_ts → build_success_ts`

### Activation KPIs

| KPI | Definition | Target |
|-----|------------|--------|
| Install → First Build Rate | % of installs completing successful build within 24h | > 60% |
| Multi-Source Activation | % of users configuring ≥2 sources within 7 days | > 30% |
| Discovery → Download Conversion | % of searches resulting in pull/build | > 40% |

### Retention KPIs

| KPI | Definition | Target |
|-----|------------|--------|
| Weekly Active Projects | Unique projects running mldata commands weekly | Growth MoM |
| Repeat Build Rate | % of builds that are rebuilds within 30 days | > 25% |
| CI Adoption Rate | % of projects running mldata in CI weekly | > 15% |

### Quality Impact KPIs

| KPI | Definition | Target |
|-----|------------|--------|
| Issue Detection Yield | Avg quality findings per build | > 2 |
| Issue Resolution Rate | % of builds with decreasing issues in 14 days | > 50% |

### Performance KPIs

| KPI | Definition | Target |
|-----|------------|--------|
| Median Build Time per GB | Build duration / dataset size | < 30s/GB |
| Cache Hit Rate | % of builds reusing cached data | > 70% |
| Failure Rate | Failed commands per 1,000 executions | < 10 |

---

## Glossary

| Term | Definition |
|------|------------|
| **Artifact** | Output file or directory produced by a build (dataset files, reports, manifests) |
| **Build** | Complete execution of the dataset pipeline producing all artifacts |
| **Connector** | Plugin that interfaces with a specific data source (HF, Kaggle, etc.) |
| **Manifest** | YAML file capturing complete build provenance and parameters |
| **Modality** | Type of data (tabular, image, audio, text, multimodal) |
| **Provenance** | Complete lineage tracking from source to final artifact |
| **Quality Report** | JSON/Markdown summary of validation checks and findings |
| **Split** | Partition of dataset (train, validation, test) |
| **Stratification** | Splitting technique preserving label distribution across splits |
| **URI** | Uniform Resource Identifier for datasets (e.g., `hf://owner/dataset`) |

---

## Traceability

This PRD traces to:
- **Source:** [Product Vision](./product-vision.md)
- **Forward:** [Epic List](./epic-list.md), [User Story Backlog](./user-story-backlog.md)

---

**End of Document**
