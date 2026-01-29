# mldata-cli v0.4.0 User Stories

## Document Control

| Field | Value |
|-------|-------|
| **Version** | 0.4.0 |
| **Date** | 2026-01-29 |
| **Author** | Noé Flandre |
| **Status** | Draft |
| **Parent Document** | [01-epic.md](./01-epic.md) |

---

## US-036: Download Resume

**Epic:** E8 - Download Reliability & Integration
**Persona:** Student / Indie Hacker

**As a** Student with limited bandwidth, **I want** interrupted downloads to resume where they left off, **so that** I don't waste progress on large datasets.

**Acceptance Criteria:**
- [ ] Partial downloads saved to temp location
- [ ] Subsequent pull detects partial and resumes
- [ ] Progress bar shows "Resuming from X%"
- [ ] Works for sources that support range requests
- [ ] Falls back to full download if resume not supported
- [ ] Resume detection works for >1GB files

**Edge Cases:**
- Source doesn't support range requests: Full re-download with warning
- Partial file corrupted: Detect, restart from beginning
- Version changed upstream: Detect via ETag, restart
- Resume fails mid-download: Fall back to full download

**UX/Behavior Notes:**
- Clear message when resuming vs starting fresh
- Show both resumed progress and total progress
- Use color to distinguish resume from fresh download

---

## US-037: File Integrity Checks

**Epic:** E8 - Download Reliability & Integration
**Persona:** ML Research Engineer

**As a** ML Research Engineer, **I want** mldata to verify that image and audio files are valid, **so that** training doesn't fail on corrupt files.

**Acceptance Criteria:**
- [ ] Verify images can be opened/decoded (JPEG, PNG)
- [ ] Verify audio files can be read (WAV, MP3, FLAC)
- [ ] Check for truncated/corrupt files
- [ ] Report corrupt file paths with line/column
- [ ] Support `mldata validate --checks files`
- [ ] Configurable timeout per file (default: 5s)

**Edge Cases:**
- Very large datasets: Sample-based checking (10%) with option for full
- Slow file system: Show progress, allow interruption
- Mixed valid/invalid: Report percentage and list first 10
- Unsupported formats: Skip with warning

**UX/Behavior Notes:**
- Show progress during file checks
- ASCII progress bar for large datasets
- Color-coded results: green (valid), yellow (skipped), red (corrupt)
- Option to move corrupt files to quarantine directory

---

## US-038: DVC Integration

**Epic:** E8 - Download Reliability & Integration
**Persona:** ML Engineer

**As a** ML Engineer, **I want** mldata to integrate with DVC, **so that** I can version datasets alongside code.

**Acceptance Criteria:**
- [ ] `mldata export --dvc` generates `.dvc` file
- [ ] Works with existing DVC remote configuration
- [ ] Tracks dataset directory or specific files
- [ ] Manifest and DVC file reference same hashes
- [ ] Clear instructions for pushing to DVC remote
- [ ] Support `mldata build --dvc` to auto-export with DVC

**Edge Cases:**
- DVC not installed: Error with install instructions
- No DVC remote configured: Warn, still create .dvc
- Existing .dvc file: Update or error with `--force`
- Not in git repo: Warn, still create .dvc file

**UX/Behavior Notes:**
- Show DVC commands to run next
- Verify DVC file created correctly
- Display git status after creation

---

## US-039: Git-LFS Integration

**Epic:** E8 - Download Reliability & Integration
**Persona:** ML Engineer

**As a** ML Engineer, **I want** mldata to configure Git-LFS tracking, **so that** large files are stored efficiently in git.

**Acceptance Criteria:**
- [ ] `mldata export --git-lfs` configures LFS tracking
- [ ] Add patterns to .gitattributes automatically
- [ ] Track Parquet, CSV, and other large files
- [ ] Works with existing .gitattributes
- [ ] Clear status of what's tracked
- [ ] Show what patterns were added

**Edge Cases:**
- Git-LFS not installed: Error with install instructions
- Not in git repo: Error with instructions
- Patterns already exist: Skip, don't duplicate
- .gitattributes readonly: Error with instructions

**UX/Behavior Notes:**
- Show what patterns were added to .gitattributes
- Suggest git commands for commit
- Display LFS storage estimate

---

## US-040: Multi-Format Export

**Epic:** E8 - Download Reliability & Integration
**Persona:** ML Research Engineer

**As a** ML Research Engineer, **I want** to export to multiple formats at once, **so that** I can support different use cases efficiently.

**Acceptance Criteria:**
- [ ] `mldata export --formats parquet,csv,jsonl` exports to all three
- [ ] All formats produced in single pass (efficient)
- [ ] Each format in separate file in artifacts/
- [ ] Manifest lists all exported formats
- [ ] Progress shows per-format completion

**Edge Cases:**
- Format fails: Continue with others, report failure
- Disk space: Check before starting, fail fast if insufficient
- Invalid format: Error with valid options listed

**UX/Behavior Notes:**
- Show progress per format with spinner
- Summary lists all output files with sizes
- Total time and throughput reported

---

## US-041: Framework Export Templates

**Epic:** E8 - Download Reliability & Integration
**Persona:** Student / Indie Hacker

**As a** Student, **I want** datasets exported in formats my framework understands, **so that** I can load them with minimal code.

**Acceptance Criteria:**
- [ ] PyTorch-compatible directory structure option
- [ ] TensorFlow tfrecord export option (future)
- [ ] Loader code snippet generated
- [ ] README with loading instructions
- [ ] `mldata export --framework pytorch` creates PyTorch structure

**Edge Cases:**
- Framework not supported: List supported frameworks
- Complex schemas: Simplify or provide custom loader
- Very large datasets: Warn about memory usage

**UX/Behavior Notes:**
- Show loading code snippet after export
- Include example in generated README
- Display framework compatibility notes

---

## Traceability Matrix

| Story | Epic | Commands | Tests |
|-------|------|----------|-------|
| US-036 | E8 | `pull` | `test_resume_*` |
| US-037 | E8 | `validate` | `test_files_*` |
| US-038 | E8 | `export --dvc` | `test_dvc_*` |
| US-039 | E8 | `export --git-lfs` | `test_lfs_*` |
| US-040 | E8 | `export --formats` | `test_multi_format_*` |
| US-041 | E8 | `export --framework` | `test_framework_*` |

---

**End of Document**
