# mldata-cli — User Story Backlog

## Document Control

| Field | Value |
|-------|-------|
| **Version** | 1.0 |
| **Date** | 2026-01-29 |
| **Author** | Noé Flandre |
| **Status** | Draft |
| **Parent Document** | [Epic List](./epic-list.md) |

---

## Story Format

Each story follows this structure:
- **ID:** Unique identifier (US-XXX)
- **Epic:** Parent epic reference
- **Persona:** Target user persona
- **Story:** As a [persona], I want [capability], so that [benefit]
- **Acceptance Criteria:** Testable conditions for completion
- **Edge Cases:** Special scenarios to handle
- **UX/Behavior Notes:** Interaction details

---

## E1: Discovery & Search (4 Stories)

### US-001: Unified Dataset Search

**Epic:** E1 - Discovery & Search
**Persona:** ML Research Engineer

**As a** ML Research Engineer, **I want** to search for datasets across HuggingFace, Kaggle, and OpenML with a single command, **so that** I don't need to visit multiple platforms to find relevant data.

**Acceptance Criteria:**
- [ ] `mldata search <query>` searches all configured sources by default
- [ ] Results display source, name, size, modality, and license
- [ ] Results are sorted by relevance
- [ ] Search completes within 5 seconds for typical queries
- [ ] Empty results show helpful message with suggestions

**Edge Cases:**
- One source times out: Show partial results with warning
- No configured sources: Error with setup instructions
- Query matches thousands: Paginate or limit with `--limit`

**UX/Behavior Notes:**
- Use Rich tables for result display
- Highlight dataset names and sources with colors
- Show result count: "Found 42 datasets (showing top 20)"

---

### US-002: Filter Search Results

**Epic:** E1 - Discovery & Search
**Persona:** Data Scientist

**As a** Data Scientist, **I want** to filter search results by modality, task, size, and license, **so that** I can quickly narrow down to datasets that fit my requirements.

**Acceptance Criteria:**
- [ ] `--source` flag filters to specific source (hf, kaggle, openml)
- [ ] `--modality` flag filters by data type (text, image, audio, tabular)
- [ ] `--task` flag filters by ML task (classification, regression, etc.)
- [ ] `--min-size` and `--max-size` filter by dataset size
- [ ] `--license` filters by license type
- [ ] Filters can be combined

**Edge Cases:**
- Invalid filter value: Show error with valid options
- No results after filtering: Suggest relaxing filters
- Source doesn't support filter: Skip gracefully, note in output

**UX/Behavior Notes:**
- Show active filters in output header
- Provide filter autocompletion in shell

---

### US-003: Dataset Information Display

**Epic:** E1 - Discovery & Search
**Persona:** ML Research Engineer

**As a** ML Research Engineer, **I want** to view detailed information about a dataset before downloading, **so that** I can verify it meets my needs.

**Acceptance Criteria:**
- [ ] `mldata info <uri>` displays comprehensive metadata
- [ ] Shows: name, description, size, license, author, last updated
- [ ] Shows: modality, task tags, download count (if available)
- [ ] Shows: schema/columns with types
- [ ] Shows: sample rows (configurable count)
- [ ] License displayed prominently with usage restrictions

**Edge Cases:**
- Dataset not found: Clear error with similar suggestions
- Partial metadata: Display available fields, note missing
- Very long descriptions: Truncate with "show more" hint

**UX/Behavior Notes:**
- Use Rich panels for organized display
- Color-code license (green=permissive, yellow=restrictive, red=unknown)
- Schema displayed as a formatted table

---

### US-004: Dataset Preview

**Epic:** E1 - Discovery & Search
**Persona:** Student / Indie Hacker

**As a** Student, **I want** to preview a few rows of a dataset without downloading the whole thing, **so that** I can quickly assess if it's what I need.

**Acceptance Criteria:**
- [ ] `mldata info <uri> --sample 10` shows 10 sample rows
- [ ] Preview fetches minimal data (streaming where possible)
- [ ] Displays data in formatted table
- [ ] Shows column types alongside data
- [ ] Works for all supported sources

**Edge Cases:**
- Dataset requires auth: Prompt for login first
- Very wide tables: Truncate columns, show full in `--json`
- Binary columns (images): Show "[image]" placeholder with path

**UX/Behavior Notes:**
- Default sample size: 5 rows
- Max sample size: 100 rows
- Use horizontal scrolling for wide tables in terminals that support it

---

## E2: Fetch & Download (6 Stories)

### US-005: Download Dataset by URI

**Epic:** E2 - Fetch & Download
**Persona:** ML Engineer

**As a** ML Engineer, **I want** to download a dataset using a simple URI, **so that** I don't need to learn different APIs for each source.

**Acceptance Criteria:**
- [ ] `mldata pull hf://owner/dataset` downloads from HuggingFace
- [ ] `mldata pull kaggle://owner/dataset` downloads from Kaggle
- [ ] `mldata pull openml://dataset-id` downloads from OpenML
- [ ] Default output: `./mldata/<dataset-name>/`
- [ ] `--output` flag overrides output location
- [ ] Download shows progress bar with ETA

**Edge Cases:**
- Invalid URI format: Error with expected format examples
- Dataset doesn't exist: Clear 404 message with suggestions
- Output directory exists: Prompt for overwrite or use `--force`

**UX/Behavior Notes:**
- Progress bar shows: downloaded/total, speed, ETA
- Completion message shows output path and size

---

### US-006: Caching Downloaded Data

**Epic:** E2 - Fetch & Download
**Persona:** ML Engineer

**As a** ML Engineer, **I want** downloads to be cached, **so that** repeated pulls don't waste bandwidth.

**Acceptance Criteria:**
- [ ] Downloaded files cached in `~/.mldata/cache/`
- [ ] Cache key = SHA-256(uri + version + params)
- [ ] Subsequent pulls use cache (show "Using cached data")
- [ ] `--no-cache` flag forces fresh download
- [ ] Cache size manageable via config (`cache.max_size_gb`)
- [ ] Old entries evicted using LRU when cache full

**Edge Cases:**
- Corrupted cache entry: Detect via hash, re-download
- Cache directory not writable: Fall back to temp, warn user
- Different version requested: Cache miss, download new version

**UX/Behavior Notes:**
- Show cache hit/miss in verbose mode
- `mldata doctor` reports cache status and size

---

### US-007: Resume Interrupted Downloads

**Epic:** E2 - Fetch & Download
**Persona:** Student / Indie Hacker

**As a** Student, **I want** interrupted downloads to resume where they left off, **so that** I don't lose progress on large datasets.

**Acceptance Criteria:**
- [ ] Partial downloads saved to temp location
- [ ] Subsequent pull detects partial and resumes
- [ ] Progress bar shows "Resuming from X%"
- [ ] Works for sources that support range requests
- [ ] Falls back to full download if resume not supported

**Edge Cases:**
- Source doesn't support range requests: Full re-download with warning
- Partial file corrupted: Detect, restart from beginning
- Version changed upstream: Detect via ETag, restart

**UX/Behavior Notes:**
- Clear message when resuming vs starting fresh
- Show both resumed progress and total progress

---

### US-008: Authentication Management

**Epic:** E2 - Fetch & Download
**Persona:** ML Engineer

**As a** ML Engineer, **I want** to configure authentication once and have it work across sessions, **so that** I don't need to re-enter credentials.

**Acceptance Criteria:**
- [ ] `mldata auth login huggingface` prompts for token
- [ ] Credentials stored in OS keyring (secure)
- [ ] Environment variables override stored credentials
- [ ] `mldata auth status` shows configured sources (no secrets)
- [ ] `mldata auth logout <source>` removes credentials
- [ ] Credentials never appear in logs or output

**Edge Cases:**
- Keyring unavailable: Fall back to config file with permission warning
- Invalid token: Clear error, prompt to re-authenticate
- Token expired: Detect and prompt for refresh

**UX/Behavior Notes:**
- `auth status` shows ✓/✗ for each source
- Token input hidden (no echo)
- Config file permissions enforced (600)

---

### US-009: Download Progress Reporting

**Epic:** E2 - Fetch & Download
**Persona:** Data Scientist

**As a** Data Scientist, **I want** clear progress indication during downloads, **so that** I know how long to wait.

**Acceptance Criteria:**
- [ ] Progress bar shows: percentage, downloaded/total, speed
- [ ] ETA calculated and displayed
- [ ] Multi-file downloads show per-file and overall progress
- [ ] Progress updates at least every second
- [ ] Completion shows total time and average speed

**Edge Cases:**
- Unknown total size: Show downloaded bytes, no percentage
- Speed drops to zero: Show "stalled" indicator
- Very fast downloads: Still show completion message

**UX/Behavior Notes:**
- Use Rich progress bars
- Show spinner for indeterminate operations
- Quiet mode (`-q`) suppresses progress, shows only result

---

### US-010: Multi-file Dataset Handling

**Epic:** E2 - Fetch & Download
**Persona:** ML Research Engineer

**As a** ML Research Engineer, **I want** to download datasets that consist of multiple files, **so that** I can work with complex datasets (images, audio, shards).

**Acceptance Criteria:**
- [ ] Automatically detect multi-file datasets
- [ ] Download all files maintaining directory structure
- [ ] Show aggregate progress (files completed, total size)
- [ ] Support `--subset` to download specific subset/config
- [ ] Verify all files after download (checksum if available)

**Edge Cases:**
- Some files fail: Report failures, continue with others, exit code 1
- Very large file count (>1000): Batch progress updates
- Subset not found: Error with available subsets listed

**UX/Behavior Notes:**
- List files being downloaded in verbose mode
- Summary shows: X files, Y GB total, Z minutes

---

## E3: Normalization (5 Stories)

### US-011: Automatic Format Detection

**Epic:** E3 - Normalization
**Persona:** Data Scientist

**As a** Data Scientist, **I want** mldata to automatically detect the format of downloaded data, **so that** I don't need to specify it manually.

**Acceptance Criteria:**
- [ ] Detect CSV, JSON, JSONL, Parquet, Arrow formats
- [ ] Detect image directories (JPEG, PNG, etc.)
- [ ] Detect audio directories (WAV, MP3, FLAC)
- [ ] Detection based on file extension and content sniffing
- [ ] Detection result shown in verbose output

**Edge Cases:**
- Ambiguous format: Use content sniffing, warn if uncertain
- Mixed formats: Report each, handle appropriately
- Unknown format: Error with supported formats listed

**UX/Behavior Notes:**
- Show "Detected format: Parquet" in output
- Format detection happens automatically during pull/build

---

### US-012: Format Conversion

**Epic:** E3 - Normalization
**Persona:** ML Engineer

**As a** ML Engineer, **I want** to convert datasets to my preferred format, **so that** I can use optimized formats for my workflow.

**Acceptance Criteria:**
- [ ] `--format parquet` converts output to Parquet
- [ ] `--format jsonl` converts output to JSON Lines
- [ ] `--format csv` converts output to CSV
- [ ] Conversion preserves all data and types
- [ ] Original schema documented in manifest

**Edge Cases:**
- Type incompatibility: Warn, use best-effort conversion
- Very large files: Stream conversion, don't load all in memory
- Binary columns: Preserve as-is or save references

**UX/Behavior Notes:**
- Show conversion progress for large datasets
- Report any type coercions in verbose mode

---

### US-013: Standardized Directory Layout

**Epic:** E3 - Normalization
**Persona:** ML Engineer

**As a** ML Engineer, **I want** all datasets to follow a standard directory structure, **so that** my scripts work consistently across datasets.

**Acceptance Criteria:**
- [ ] Output follows standardized layout (see technical-design.md)
- [ ] manifest.yaml at root
- [ ] reports/ directory for quality reports
- [ ] splits/ directory for train/val/test files
- [ ] artifacts/ directory for exported formats
- [ ] raw/ directory for original files (optional)

**Edge Cases:**
- Existing directory structure: Reorganize or error with `--force`
- Very large raw files: Option to skip copying raw

**UX/Behavior Notes:**
- Layout described in docs and `mldata doctor` output
- Tree view of output shown after build

---

### US-014: Schema Inference

**Epic:** E3 - Normalization
**Persona:** Data Scientist

**As a** Data Scientist, **I want** mldata to infer and document the dataset schema, **so that** I understand the data structure.

**Acceptance Criteria:**
- [ ] Infer column names and types from data
- [ ] Schema saved in manifest.yaml
- [ ] Schema shown in `mldata info` output
- [ ] Support common types: string, int, float, bool, datetime, binary
- [ ] Detect nullable columns

**Edge Cases:**
- Mixed types in column: Infer as string, warn
- Very wide schemas (>100 columns): Summarize in output
- No clear schema (unstructured): Note as unstructured

**UX/Behavior Notes:**
- Schema displayed as table with column, type, nullable, description
- Use Polars type inference

---

### US-015: Multimodal Data Handling

**Epic:** E3 - Normalization
**Persona:** ML Research Engineer

**As a** ML Research Engineer, **I want** mldata to handle datasets with images and audio properly, **so that** references are maintained correctly.

**Acceptance Criteria:**
- [ ] Image paths preserved as relative references
- [ ] Audio paths preserved as relative references
- [ ] File existence validated during normalization
- [ ] Metadata (dimensions, duration) extracted and stored
- [ ] Support for embedded vs referenced media

**Edge Cases:**
- Missing referenced files: Warn, continue or fail based on config
- Very large media files: Stream, don't load into memory
- Unsupported media format: Skip with warning

**UX/Behavior Notes:**
- Show media statistics: "Found 10,000 images, 5 missing"
- Thumbnail generation optional for preview

---

## E4: Quality Validation (6 Stories)

### US-016: Duplicate Detection

**Epic:** E4 - Quality Validation
**Persona:** ML Research Engineer

**As a** ML Research Engineer, **I want** mldata to detect duplicate samples, **so that** I can remove them and avoid inflated metrics.

**Acceptance Criteria:**
- [ ] Detect exact duplicates (hash-based)
- [ ] Detect near-duplicates (similarity threshold)
- [ ] Report duplicate count and example pairs
- [ ] Configurable similarity threshold (default: 0.95)
- [ ] Support text, tabular, and image duplicates

**Edge Cases:**
- Very large datasets: Use efficient algorithms (MinHash, LSH)
- No duplicates: Report "No duplicates found" (success)
- Threshold too low: Warn about false positives

**UX/Behavior Notes:**
- Show top 5 duplicate pairs in report
- Suggest deduplication if >1% duplicates

---

### US-017: Label Distribution Analysis

**Epic:** E4 - Quality Validation
**Persona:** Data Scientist

**As a** Data Scientist, **I want** mldata to analyze label distribution, **so that** I can identify class imbalance issues.

**Acceptance Criteria:**
- [ ] Count samples per class/label
- [ ] Calculate imbalance ratio (max/min)
- [ ] Flag severe imbalance (configurable threshold)
- [ ] Show distribution as table and/or histogram
- [ ] Support multi-label scenarios

**Edge Cases:**
- No label column: Skip check, note in report
- Many classes (>100): Summarize, show top/bottom
- Continuous labels: Treat as regression, show distribution stats

**UX/Behavior Notes:**
- ASCII histogram in terminal
- Suggest techniques for imbalanced data

---

### US-018: Missing Value Detection

**Epic:** E4 - Quality Validation
**Persona:** Data Scientist

**As a** Data Scientist, **I want** mldata to detect missing values, **so that** I can decide how to handle them.

**Acceptance Criteria:**
- [ ] Count null/NaN/empty values per column
- [ ] Calculate missing percentage per column
- [ ] Flag columns exceeding threshold (default: 5%)
- [ ] Identify rows with any missing values
- [ ] Report total missing vs total cells

**Edge Cases:**
- All values missing in column: Flag as critical
- Empty strings vs null: Distinguish in config
- Sparse datasets: Report sparsity percentage

**UX/Behavior Notes:**
- Table showing column, missing count, missing %
- Color code: green (<1%), yellow (1-5%), red (>5%)

---

### US-019: Schema Validation

**Epic:** E4 - Quality Validation
**Persona:** ML Engineer

**As a** ML Engineer, **I want** mldata to validate schema consistency, **so that** I catch type mismatches before training.

**Acceptance Criteria:**
- [ ] Verify consistent types across all rows
- [ ] Check schema matches across splits (train/val/test)
- [ ] Detect unexpected null values in non-nullable columns
- [ ] Validate against expected schema if provided
- [ ] Report type coercions and mismatches

**Edge Cases:**
- Different schemas per split: Error, require reconciliation
- Dynamic schemas (JSON): Validate common fields
- Binary columns: Skip type validation

**UX/Behavior Notes:**
- Show schema diff if splits don't match
- Suggest schema fixes

---

### US-020: File Integrity Checks

**Epic:** E4 - Quality Validation
**Persona:** ML Research Engineer

**As a** ML Research Engineer, **I want** mldata to verify that image and audio files are valid, **so that** training doesn't fail on corrupt files.

**Acceptance Criteria:**
- [ ] Verify images can be opened/decoded
- [ ] Verify audio files can be read
- [ ] Check for truncated/corrupt files
- [ ] Report corrupt file paths
- [ ] Verify file sizes are reasonable

**Edge Cases:**
- Very large datasets: Sample-based checking with option for full
- Slow file system: Show progress, allow interruption
- Mixed valid/invalid: Report percentage and list

**UX/Behavior Notes:**
- Show progress during file checks
- Option to move corrupt files to quarantine directory

---

### US-021: Quality Report Generation

**Epic:** E4 - Quality Validation
**Persona:** ML Engineer

**As a** ML Engineer, **I want** quality reports in both human-readable and machine-readable formats, **so that** I can review manually and parse in CI.

**Acceptance Criteria:**
- [ ] Generate JSON report (schema-compliant)
- [ ] Generate Markdown report (human-readable)
- [ ] Reports saved to `reports/` directory
- [ ] Include summary and detailed findings
- [ ] Include suggestions for each issue

**Edge Cases:**
- No issues found: Generate report noting "All checks passed"
- Report write fails: Error clearly, don't lose findings
- Very long reports: Paginate or summarize

**UX/Behavior Notes:**
- Show report path after generation
- Summary printed to terminal regardless of format

---

## E5: Splitting (4 Stories)

### US-022: Basic Train/Val/Test Split

**Epic:** E5 - Splitting
**Persona:** Data Scientist

**As a** Data Scientist, **I want** to split datasets into train/val/test sets, **so that** I can properly evaluate my models.

**Acceptance Criteria:**
- [ ] `mldata split <path>` creates splits with default ratios (0.8/0.1/0.1)
- [ ] `--ratios 0.7,0.2,0.1` customizes split ratios
- [ ] Splits are mutually exclusive (no overlap)
- [ ] Split sizes match ratios (within 1 sample)
- [ ] Split files saved as indices or separate files

**Edge Cases:**
- Very small datasets: Warn if any split < 10 samples
- Ratios don't sum to 1: Auto-normalize, warn
- Single split requested: Allow with warning

**UX/Behavior Notes:**
- Show split sizes after completion
- Confirm ratios before processing large datasets

---

### US-023: Stratified Splitting

**Epic:** E5 - Splitting
**Persona:** ML Research Engineer

**As a** ML Research Engineer, **I want** stratified splits that preserve label distribution, **so that** each split is representative.

**Acceptance Criteria:**
- [ ] `--stratify <column>` enables stratified splitting
- [ ] Each split maintains same label proportions (within tolerance)
- [ ] Works with multi-class classification
- [ ] Reports label distribution per split
- [ ] Fails gracefully if stratification impossible (rare classes)

**Edge Cases:**
- Class with 1 sample: Warn, place in train by default
- Very many classes: Still stratify, may have empty strata
- Multi-label: Stratify on primary label or distribution

**UX/Behavior Notes:**
- Show label distribution comparison after split
- Warn if stratification significantly differs from requested ratios

---

### US-024: Deterministic Seeding

**Epic:** E5 - Splitting
**Persona:** ML Engineer

**As a** ML Engineer, **I want** splits to be reproducible with a seed, **so that** experiments are comparable.

**Acceptance Criteria:**
- [ ] `--seed 42` produces identical splits every time
- [ ] Default seed is random but recorded in manifest
- [ ] Seed stored in manifest for reproducibility
- [ ] Same seed + same data = same splits (guaranteed)
- [ ] Different seeds produce different splits

**Edge Cases:**
- Data order changed: Same seed may produce different results (document)
- Seed not specified: Generate random, warn in CI mode

**UX/Behavior Notes:**
- Always show seed in output: "Split with seed: 42"
- Manifest includes seed for rebuild

---

### US-025: Split Index Files

**Epic:** E5 - Splitting
**Persona:** ML Engineer

**As a** ML Engineer, **I want** split assignments exported as index files, **so that** I can use them with any framework.

**Acceptance Criteria:**
- [ ] Generate `splits/train.csv`, `val.csv`, `test.csv` with indices
- [ ] Support index-only format (just row numbers)
- [ ] Support ID-based format (if ID column exists)
- [ ] Export as CSV, JSON, or text (one ID per line)
- [ ] Include metadata (seed, ratios) in split files

**Edge Cases:**
- No unique ID column: Use row indices with warning
- Very large splits: Stream write, don't hold in memory
- Request specific format: Honor format preference

**UX/Behavior Notes:**
- Show split file paths after generation
- Index files are lightweight and git-friendly

---

## E6: Export & Versioning (6 Stories)

### US-026: Parquet Export

**Epic:** E6 - Export & Versioning
**Persona:** ML Engineer

**As a** ML Engineer, **I want** to export datasets as Parquet, **so that** I get efficient storage and fast loading.

**Acceptance Criteria:**
- [ ] `mldata export <path> --format parquet` exports to Parquet
- [ ] Support compression options (snappy, gzip, zstd)
- [ ] Preserve schema and types exactly
- [ ] Row groups sized for efficient reading
- [ ] Metadata preserved in Parquet footer

**Edge Cases:**
- Very wide tables: Handle up to 1000 columns
- Nested types: Flatten or preserve based on config
- Large files: Partition automatically or warn

**UX/Behavior Notes:**
- Show output file size and compression ratio
- Default compression: snappy (good balance)

---

### US-027: JSONL Export

**Epic:** E6 - Export & Versioning
**Persona:** Data Scientist

**As a** Data Scientist, **I want** to export datasets as JSON Lines, **so that** I can use them with NLP tools.

**Acceptance Criteria:**
- [ ] `mldata export <path> --format jsonl` exports to JSONL
- [ ] One JSON object per line
- [ ] Support gzip compression (`.jsonl.gz`)
- [ ] UTF-8 encoding guaranteed
- [ ] Preserve all field types (dates as ISO strings)

**Edge Cases:**
- Binary fields: Base64 encode or skip with warning
- Very long lines: No line length limit, but warn >1MB
- Special characters: Proper JSON escaping

**UX/Behavior Notes:**
- Show line count and file size after export
- Option for pretty-printed JSON (not lines)

---

### US-028: Multiple Format Export

**Epic:** E6 - Export & Versioning
**Persona:** ML Research Engineer

**As a** ML Research Engineer, **I want** to export to multiple formats at once, **so that** I can support different use cases.

**Acceptance Criteria:**
- [ ] `--format parquet,jsonl,csv` exports to all three
- [ ] All formats produced in single pass (efficient)
- [ ] Each format in separate file in artifacts/
- [ ] Manifest lists all exported formats

**Edge Cases:**
- Format fails: Continue with others, report failure
- Disk space: Check before starting, fail fast if insufficient

**UX/Behavior Notes:**
- Show progress per format
- Summary lists all output files

---

### US-029: DVC Integration

**Epic:** E6 - Export & Versioning
**Persona:** ML Engineer

**As a** ML Engineer, **I want** mldata to integrate with DVC, **so that** I can version datasets alongside code.

**Acceptance Criteria:**
- [ ] `mldata export --dvc` generates `.dvc` file
- [ ] Works with existing DVC remote configuration
- [ ] Tracks dataset directory or specific files
- [ ] Manifest and DVC file reference same hashes
- [ ] Clear instructions for pushing to DVC remote

**Edge Cases:**
- DVC not installed: Error with install instructions
- No DVC remote configured: Warn, still create .dvc
- Existing .dvc file: Update or error with `--force`

**UX/Behavior Notes:**
- Show DVC commands to run next
- Verify DVC file created correctly

---

### US-030: Git-LFS Integration

**Epic:** E6 - Export & Versioning
**Persona:** ML Engineer

**As a** ML Engineer, **I want** mldata to configure Git-LFS tracking, **so that** large files are stored efficiently.

**Acceptance Criteria:**
- [ ] `mldata export --git-lfs` configures LFS tracking
- [ ] Add patterns to .gitattributes
- [ ] Track Parquet and other large files
- [ ] Works with existing .gitattributes
- [ ] Clear status of what's tracked

**Edge Cases:**
- Git-LFS not installed: Error with install instructions
- Not in git repo: Error with instructions
- Patterns already exist: Skip, don't duplicate

**UX/Behavior Notes:**
- Show what patterns were added
- Suggest git commands for commit

---

### US-031: Framework-Specific Export

**Epic:** E6 - Export & Versioning
**Persona:** Student / Indie Hacker

**As a** Student, **I want** datasets exported in formats my framework understands, **so that** I can load them with minimal code.

**Acceptance Criteria:**
- [ ] PyTorch-compatible directory structure option
- [ ] TensorFlow tfrecord export option (future)
- [ ] Loader code snippet generated
- [ ] README with loading instructions

**Edge Cases:**
- Framework not supported: List supported frameworks
- Complex schemas: Simplify or provide custom loader

**UX/Behavior Notes:**
- Show loading code snippet after export
- Include example in generated README

---

## E7: Rebuild & Diff (4 Stories)

### US-032: Rebuild from Manifest

**Epic:** E7 - Rebuild & Diff
**Persona:** ML Engineer

**As a** ML Engineer, **I want** to rebuild a dataset from its manifest, **so that** I can reproduce exact dataset state.

**Acceptance Criteria:**
- [ ] `mldata rebuild manifest.yaml` recreates dataset
- [ ] Uses same source, version, parameters from manifest
- [ ] Applies same normalization, validation, splitting, export
- [ ] Output matches original (verifiable by hash)
- [ ] Works even if source has newer versions

**Edge Cases:**
- Source unavailable: Clear error, suggest alternatives
- Cached data stale: Re-download from source
- Manifest version incompatible: Warn, attempt best-effort

**UX/Behavior Notes:**
- Show "Rebuilding from manifest created on <date>"
- Progress mirrors original build

---

### US-033: Build Verification

**Epic:** E7 - Rebuild & Diff
**Persona:** ML Engineer

**As a** ML Engineer, **I want** rebuilds to be verified against original hashes, **so that** I have confidence in reproducibility.

**Acceptance Criteria:**
- [ ] `--verify` flag (default: true) checks output hashes
- [ ] Compare each artifact hash against manifest
- [ ] Report match/mismatch for each file
- [ ] Exit code 0 if all match, 1 if mismatch
- [ ] Detail which files differ if verification fails

**Edge Cases:**
- Hash algorithm changed: Support multiple algorithms
- Floating point differences: Note as acceptable variance
- Non-deterministic source: Warn, skip verification

**UX/Behavior Notes:**
- Show ✓/✗ for each file
- Summary: "Verification: 5/5 files match"

---

### US-034: Manifest Generation

**Epic:** E7 - Rebuild & Diff
**Persona:** ML Research Engineer

**As a** ML Research Engineer, **I want** comprehensive manifests capturing all build details, **so that** nothing is lost for reproducibility.

**Acceptance Criteria:**
- [ ] Manifest generated automatically on every build
- [ ] Includes: source URI, version, fetch timestamp
- [ ] Includes: all parameters (seed, ratios, format, checks)
- [ ] Includes: all artifact hashes (SHA-256)
- [ ] Includes: tool version, Python version, OS
- [ ] Human-readable YAML format

**Edge Cases:**
- Build fails: Don't write manifest (or mark as failed)
- Partial build: Include what was completed
- Manifest exists: Overwrite with warning or `--force`

**UX/Behavior Notes:**
- Show manifest path after build
- Manifest is git-friendly (diffable)

---

### US-035: Dataset Diff

**Epic:** E7 - Rebuild & Diff
**Persona:** ML Engineer

**As a** ML Engineer, **I want** to compare two dataset builds, **so that** I understand what changed.

**Acceptance Criteria:**
- [ ] `mldata diff manifest1.yaml manifest2.yaml` compares builds
- [ ] Show: parameter changes (seed, ratios, etc.)
- [ ] Show: row count changes per split
- [ ] Show: label distribution changes
- [ ] Show: hash differences (which files changed)
- [ ] Support `--detailed` for row-level diff

**Edge Cases:**
- Different sources: Warn, still compare
- Incomparable formats: Error, suggest conversion
- Very large diffs: Summarize, provide detailed in file

**UX/Behavior Notes:**
- Color-coded diff output (added=green, removed=red)
- Summary first, details on request

---

## Traceability Matrix

| Story | Epic | PRD Req | Commands | Tests |
|-------|------|---------|----------|-------|
| US-001 | E1 | FR1 | `search` | `test_search_*` |
| US-002 | E1 | FR1 | `search` | `test_search_filters_*` |
| US-003 | E1 | FR1 | `info` | `test_info_*` |
| US-004 | E1 | FR1 | `info --sample` | `test_preview_*` |
| US-005 | E2 | FR2 | `pull` | `test_pull_*` |
| US-006 | E2 | FR3 | `pull` | `test_cache_*` |
| US-007 | E2 | FR3 | `pull` | `test_resume_*` |
| US-008 | E2 | FR2 | `auth` | `test_auth_*` |
| US-009 | E2 | FR2 | `pull` | `test_progress_*` |
| US-010 | E2 | FR2 | `pull` | `test_multifile_*` |
| US-011 | E3 | FR4 | `pull`, `build` | `test_format_detect_*` |
| US-012 | E3 | FR5 | `export`, `build` | `test_convert_*` |
| US-013 | E3 | FR4 | `build` | `test_layout_*` |
| US-014 | E3 | FR4 | `build`, `info` | `test_schema_*` |
| US-015 | E3 | FR4 | `build` | `test_multimodal_*` |
| US-016 | E4 | FR6 | `validate` | `test_duplicates_*` |
| US-017 | E4 | FR7 | `validate` | `test_labels_*` |
| US-018 | E4 | FR7 | `validate` | `test_missing_*` |
| US-019 | E4 | FR8 | `validate` | `test_schema_val_*` |
| US-020 | E4 | FR8 | `validate` | `test_files_*` |
| US-021 | E4 | FR6-8 | `validate` | `test_report_*` |
| US-022 | E5 | FR9 | `split` | `test_split_basic_*` |
| US-023 | E5 | FR10 | `split` | `test_stratify_*` |
| US-024 | E5 | FR9 | `split` | `test_seed_*` |
| US-025 | E5 | FR9 | `split` | `test_indices_*` |
| US-026 | E6 | FR11 | `export` | `test_parquet_*` |
| US-027 | E6 | FR11 | `export` | `test_jsonl_*` |
| US-028 | E6 | FR11 | `export` | `test_multi_format_*` |
| US-029 | E6 | FR12 | `export --dvc` | `test_dvc_*` |
| US-030 | E6 | FR12 | `export --git-lfs` | `test_lfs_*` |
| US-031 | E6 | FR11 | `export` | `test_framework_*` |
| US-032 | E7 | FR14 | `rebuild` | `test_rebuild_*` |
| US-033 | E7 | FR14 | `rebuild` | `test_verify_*` |
| US-034 | E7 | FR13 | `build` | `test_manifest_*` |
| US-035 | E7 | FR15 | `diff` | `test_diff_*` |

---

**End of Document**
