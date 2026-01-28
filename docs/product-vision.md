# mldata-cli — Product Vision & Problem Statement 

**Document type:** Product Vision / Problem Statement / KPI Framework  
**Product:** mldata-cli (working name)  
**Version:** v0.1 (draft)  
**Status:** Proposal  
**Author:** Noé Flandre  
**Date:** 2026-01-29  
**Audience:** Product, Engineering, Design, DevRel, GTM, OSS maintainers

---

## 1) Executive Summary

Modern ML development frequently begins with “find a dataset and make it train-ready.” In practice, this workflow is fragmented across multiple platforms (Hugging Face, Kaggle, OpenML, UCI, AWS Open Data, custom buckets) and multiple tool categories (downloaders, preprocessing scripts, validation frameworks, versioning systems). The result is slow iteration, non-reproducible dataset builds, hidden data quality issues, and brittle pipelines.

**mldata-cli** is proposed as a unified, reproducible dataset CLI that standardizes the dataset lifecycle:
**Discover → Fetch → Normalize → Validate → Split → Export → Version → Rebuild**
across popular dataset ecosystems and custom sources, with consistent commands, manifests, and quality reports.

The product aims to become the dataset equivalent of `git clone` + `make`: a single interface that turns “dataset reference” into “versioned, validated, train/val/test artifact” reliably and repeatedly.

---

## 2) Product Vision

### 2.1 Vision statement
**mldata-cli becomes the canonical command-line interface for dataset acquisition and preparation in ML workflows—source-agnostic, reproducible, and quality-aware by default.**

### 2.2 Mission
Enable ML builders to produce **train-ready, versioned datasets** in minutes—not days—without stitching together multiple CLIs, scripts, and ad-hoc checks.

### 2.3 Product principles
1. **Unified UX, pluggable backends:** One command set across multiple data sources.
2. **Reproducibility-first:** Every dataset build is defined by a manifest and is rebuildable.
3. **Quality by default:** Validation and profiling are part of the “build,” not an afterthought.
4. **CI-friendly:** Non-interactive operation, deterministic outputs, structured logs/artifacts.
5. **Composable:** Works standalone or integrates with DVC/Git-LFS, pipelines, and MLOps.
6. **Opinionated defaults, configurable depth:** Fast “happy path,” deeper controls when needed.

---

## 3) Problem Statement

### 3.1 Core problem (single sentence)
**It is unnecessarily hard to reliably transform “a dataset somewhere” into “a standardized, validated, train/val/test-ready dataset artifact” across sources in a reproducible way.**

### 3.2 Market gap
While tools exist in each category, **none provide a single, coherent CLI** that covers:
- multi-source dataset discovery and retrieval,
- preprocessing and format normalization,
- dataset quality checks and reporting,
- deterministic splitting,
- and data versioning integration,
all through one interface with consistent semantics.

### 3.3 Why current workflows fail
**Fragmentation:**  
- Each platform has its own APIs/CLIs and authentication patterns.
- Metadata varies widely; dataset “IDs” and versioning semantics differ.

**Non-standard data preparation:**  
- Preprocessing often lives in untracked notebooks or repo-local scripts.
- Formats vary (CSV/JSONL/Parquet/Arrow/images/audio), causing repeated conversions.

**Quality issues are discovered late:**  
- Duplicates, leakage, label imbalance, missing data, schema drift, or broken files are often detected during training or evaluation—not at ingestion time.

**Reproducibility is brittle:**  
- People download data once, mutate it locally, and forget steps.
- Teams cannot reliably reconstruct “the dataset used in experiment X” later.

---

## 4) Product Scope Overview

### 4.1 In-scope (core capabilities)
1. **Discovery**
   - Search datasets across supported sources with consistent filtering
   - Preview metadata (size, schema hints, modalities, licenses, task tags)
2. **Fetch / Download**
   - Pull datasets by source reference (e.g., `hf://`, `kaggle://`, `openml://`, `s3://`)
   - Caching and resuming downloads
3. **Normalize / Preprocess**
   - Standardize directory layout and dataset schema representation
   - Multi-format conversion (CSV/JSONL/Parquet; optionally Arrow)
4. **Quality checks**
   - Duplicate detection
   - Label distribution analysis
   - Missingness and basic schema checks
   - File integrity checks for multimodal datasets (images/audio)
5. **Splitting**
   - Train/val/test split generation
   - Stratification (classification) and deterministic seeding
6. **Versioning integration**
   - Dataset build artifacts tracked via DVC and/or Git-LFS (integration layer)
   - Dataset manifest + hashes for reproducibility
7. **Rebuilds and diffs**
   - Rebuild from manifest
   - Detect changes from upstream or preprocessing changes
   - Produce diff summary (row count, label distro changes, etc.)

### 4.2 Out-of-scope (initially)
- End-to-end model training orchestration (leave to trainers)
- Full ETL/warehouse workflows (dbt/Spark-scale transformations)
- Labeling and annotation platforms
- Sensitive/regulated data governance features (beyond basic controls)
- Enterprise identity, policy management, approvals (later phase)

---

## 5) Target Users

### 5.1 Primary segments
1. **AI/ML Research Engineers**
   - Build benchmark suites quickly across sources
   - Need reproducible dataset snapshots and quality checks
2. **ML Engineers (startup/scale-up)**
   - Need CI-ready pipelines and dataset versioning tied to releases
   - Value strong caching, determinism, integration with Git/DVC
3. **Data Scientists transitioning to production ML**
   - Want simpler “one command to get train-ready data”
   - Need guardrails to catch common issues early

### 5.2 Secondary segments
4. **Students / indie hackers**
   - Speed + simplicity matters
   - Minimal setup; easy exports for common frameworks

---

## 6) User Jobs-To-Be-Done (JTBD)

### JTBD-1: “Get a dataset fast, correctly”
**When** I need a dataset for an experiment,  
**I want** to discover and pull it from any major source with one CLI,  
**So that** I can start modeling quickly without spending hours on plumbing.

### JTBD-2: “Make it train-ready and comparable”
**When** I’m running experiments,  
**I want** deterministic splits and consistent formats,  
**So that** comparisons are fair and results are reproducible.

### JTBD-3: “Trust the data”
**When** I use external datasets,  
**I want** automatic quality checks and reports,  
**So that** I catch duplicates, leakage risks, and label issues before training.

### JTBD-4: “Rebuild the exact same dataset later”
**When** I publish results or ship a model,  
**I want** versioned dataset artifacts and manifests,  
**So that** anyone can reproduce the dataset build in CI months later.

---

## 7) Core Problem Decomposition

### 7.1 Source fragmentation (discovery & access)
- Different identifiers, schemas, auth methods, rate limits
- Inconsistent metadata; inconsistent dataset version semantics

### 7.2 Preparation fragmentation (preprocessing & conversion)
- Scripts are bespoke and rarely documented
- Data formats incompatible with downstream frameworks
- Missing consistent dataset layout conventions

### 7.3 Quality blind spots
- Duplicate samples inflate metrics
- Label imbalance causes misleading accuracy
- Missing or corrupt files break training at runtime
- Schema drift or inconsistent types cause silent bugs

### 7.4 Versioning disconnect
- Downloading and versioning are separate concerns in existing flows
- Dataset snapshots not tied to preprocessing steps and checks
- Hard to diff dataset builds across time or experiments

---

## 8) Desired Outcomes

### 8.1 User outcomes
1. **Reduced time-to-train-ready dataset**  
   Users can go from dataset reference to train/val/test-ready outputs in minutes.
2. **Higher data reliability**  
   Common dataset issues are flagged automatically before training.
3. **Reproducible experiments**  
   Dataset builds are re-runnable from a manifest with deterministic outputs.
4. **Standardized dataset artifacts**  
   Consistent folder structure + export formats; easy framework integration.
5. **Cross-source parity**  
   Same commands and mental model for HF, Kaggle, OpenML, custom sources.

### 8.2 Business/OSS outcomes
1. **High activation & retention**  
   Users repeatedly use the CLI across projects and in CI.
2. **Ecosystem extensibility**  
   Connectors and checkers are pluggable; community can add sources.
3. **Positioning as “dataset layer”**  
   Becomes the standard entrypoint in ML repos for dataset management.

---

## 9) Product Definition (Conceptual)

### 9.1 What “a dataset build” means
A **dataset build** is a deterministic function of:
- a dataset source reference (e.g., `hf://owner/dataset@revision`),
- preprocessing directives (filters, transforms, normalization),
- splitting strategy (ratios, stratification, seed),
- quality check configuration,
- export configuration,
- and environment constraints (tool version, library versions).

### 9.2 Core artifact outputs
A successful build should produce:
- **Dataset artifact** (standardized local directory + exported formats)
- **Manifest** (source, parameters, checks run, versions, hashes)
- **Quality report** (human-readable + machine-readable JSON)
- **Split files** (indices or lists mapping samples to splits)
- **Cache metadata** (to avoid repeated downloads/transforms)

### 9.3 Standardized local layout (example)
data/
mldata/
<dataset-name>/
manifest.yaml
reports/
quality.json
quality.md
splits/
train.csv
val.csv
test.csv
artifacts/
dataset.parquet
dataset.jsonl
raw/ # optional cached upstream downloads
intermediate/ # optional transform outputs


---

## 10) Success Metrics (KPIs)

> KPI design includes: **definition**, **why it matters**, **measurement method**, and **leading vs lagging** indicators.

### 10.1 North Star Metric
#### NSM: Time-to-Train-Ready Dataset (TTRD)
- **Definition:** Median elapsed time from initiating a dataset build to producing a train-ready artifact (splits + exports + manifest + quality report).
- **Why it matters:** Directly measures the core value proposition: speed + readiness.
- **Measurement:** CLI telemetry (opt-in) or local logs; `build_start_ts → build_success_ts`.
- **Type:** Lagging indicator (outcome).

**Target (initial):**
- Local cached: < 60 seconds median for medium datasets
- Fresh download: source-dependent; optimize for “fast enough” with streaming/caching

---

### 10.2 Activation & Adoption KPIs
#### A1: Install → First Successful Build Rate
- **Definition:** % of new installs that complete a successful `mldata build` within 24 hours.
- **Why:** Measures onboarding friction and product clarity.
- **Measurement:** Telemetry event `install` + `build_success`.
- **Type:** Leading indicator.

#### A2: Multi-Source Connector Activation Rate
- **Definition:** % of active users who configure ≥2 sources within 7 days (e.g., HF + Kaggle).
- **Why:** Validates unified interface value.
- **Measurement:** Events `connector_configured`.
- **Type:** Leading indicator.

#### A3: Discovery → Download Conversion
- **Definition:** % of dataset searches that result in a `pull/build` for a selected dataset.
- **Why:** Indicates discovery UX relevance and metadata usefulness.
- **Measurement:** `search` events correlated with subsequent `build`.
- **Type:** Leading indicator.

---

### 10.3 Retention & Engagement KPIs
#### R1: Weekly Active Projects (WAP)
- **Definition:** Count of unique projects (e.g., repo root fingerprints) that run mldata commands weekly.
- **Why:** Captures habitual usage across work.
- **Measurement:** Telemetry project ID; local config fingerprint (privacy-safe).
- **Type:** Lagging indicator.

#### R2: Repeat Build Rate
- **Definition:** % of builds that are rebuilds of an existing manifest (same dataset ID) within 30 days.
- **Why:** Indicates reproducibility and CI usage.
- **Measurement:** `build_from_manifest` events.
- **Type:** Lagging indicator.

#### R3: CI Adoption Rate
- **Definition:** % of projects running mldata in CI at least once per week.
- **Why:** Strong signal of “production readiness” and stickiness.
- **Measurement:** Detect CI environment variables; event tagging.
- **Type:** Lagging indicator.

---

### 10.4 Data Quality Impact KPIs
#### Q1: Issue Detection Yield
- **Definition:** Average number of unique quality findings per dataset build (e.g., duplicates found, missing labels, corrupt files).
- **Why:** Validates that quality checks provide actionable value.
- **Measurement:** `quality_findings_count` from report JSON.
- **Type:** Leading indicator (for user value).

#### Q2: Issue Resolution Rate
- **Definition:** % of builds where detected issues decrease in a subsequent build within 14 days.
- **Why:** Measures whether findings are acted upon.
- **Measurement:** Compare consecutive reports for same dataset; trend analysis.
- **Type:** Lagging indicator.

#### Q3: Prevented Training Failures (proxy)
- **Definition:** Reduction in “build succeeded but downstream training failed due to data errors.”
- **Why:** Ultimate quality ROI.
- **Measurement:** Optional integration hooks; user-reported or CI logs.
- **Type:** Lagging, harder to measure—use as proxy.

---

### 10.5 Reproducibility & Versioning KPIs
#### V1: Versioned Build Share
- **Definition:** % of dataset builds tracked using a versioning backend (DVC/Git-LFS integration enabled).
- **Why:** Validates “dataset lifecycle” positioning.
- **Measurement:** config detection + event `versioning_enabled`.
- **Type:** Leading-to-lagging hybrid.

#### V2: Reproducible Build Rate
- **Definition:** % of rebuilds that produce identical hashes/manifests when inputs are unchanged.
- **Why:** Measures determinism and trust.
- **Measurement:** compare artifact hash + manifest hash.
- **Type:** Lagging indicator.

#### V3: Dataset Diff Usage
- **Definition:** % of users who run `mldata diff` or view diff reports between builds.
- **Why:** Indicates maturity of workflow and value of versioning.
- **Measurement:** event `diff_run`.
- **Type:** Leading indicator.

---

### 10.6 Performance & Reliability KPIs
#### P1: Median Build Time per GB
- **Definition:** Median build duration normalized by dataset size.
- **Why:** Ensures scalability and user satisfaction.
- **Measurement:** `build_duration / dataset_size_gb`.
- **Type:** Lagging indicator.

#### P2: Cache Hit Rate
- **Definition:** % of builds that reuse cached upstream downloads or transform outputs.
- **Why:** Drives speed improvements and lower bandwidth costs.
- **Measurement:** event `cache_hit`.
- **Type:** Leading indicator.

#### P3: Failure Rate per 1,000 Runs
- **Definition:** Number of failed commands per 1,000 command executions.
- **Why:** Tracks stability and regressions.
- **Measurement:** error events with codes.
- **Type:** Leading indicator.

---

## 11) Product Positioning (Concise)

### 11.1 Category
**Dataset Operations CLI** (dataset lifecycle management)  
Positioned between:
- platform-specific dataset CLIs,
- data versioning tools,
- and data quality validation frameworks.

### 11.2 Differentiators
1. **Cross-source unification:** One UX across HF/Kaggle/OpenML/custom.
2. **Train-ready by default:** Splits + exports included, not DIY.
3. **Quality checks integrated:** Reports are part of the build artifact.
4. **Reproducible manifests:** Built-in provenance tracking.
5. **Versioning integration:** Optional, seamless handoff to DVC/Git-LFS.

---

## 12) Assumptions & Risks

### 12.1 Key assumptions
- Users want a single dataset entrypoint across sources (not just one ecosystem).
- A strong “happy path” with defaults will beat flexibility-first designs.
- Quality checks that are fast and lightweight will be widely adopted.

### 12.2 Key risks
- **Auth complexity:** Kaggle tokens, HF tokens, and others may create onboarding friction.
- **Licensing variance:** Datasets have diverse licenses; compliance messaging must be clear.
- **Scope creep:** Quality checks can expand into full data validation platforms.
- **Performance constraints:** Duplicate detection on large datasets can be expensive—need scalable strategies.
- **Source churn:** APIs and catalogs evolve; connector maintenance is ongoing.

### 12.3 Mitigations (strategic)
- Provide connector diagnostics and a “doctor” command.
- Start with lightweight checks; add deeper checks as optional profiles.
- Design connectors as plugins with versioned contracts.
- Cache aggressively; support streaming-based processing where possible.

---

## 13) Clear Definition of “Success” (First 6–12 Months)

**mldata-cli is successful if:**
1. Users consistently use it to build datasets from **at least 2 sources** with a unified workflow.
2. Most builds generate **deterministic splits + manifests + quality reports**.
3. Teams adopt it in **CI** for reproducible dataset builds.
4. The CLI becomes a recognizable “dataset layer” in ML repos and templates.

---

## 14) Appendix — Example “What success looks like” (User story)

> “I searched for a sentiment dataset, pulled it from Hugging Face, ran standard checks, got stratified splits, exported Parquet, and versioned it with DVC—then my teammate rebuilt the exact same dataset from the manifest in CI.”

---

**End of document**