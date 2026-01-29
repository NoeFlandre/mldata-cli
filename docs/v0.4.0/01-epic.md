# mldata-cli v0.4.0 Epic

## Document Control

| Field | Value |
|-------|-------|
| **Version** | 0.4.0 |
| **Date** | 2026-01-29 |
| **Author** | Noé Flandre |
| **Status** | Draft |
| **Parent Document** | [Epic List](../epic-list.md) |

---

## Epic Overview

**Epic:** E8 - Download Reliability & Integration
**Theme:** Resume downloads, file integrity, and external integrations

### Goals
- Enable reliable downloads with resume capability
- Validate file integrity for media datasets
- Integrate with DVC and Git-LFS for versioning
- Export to framework-specific formats

---

## Scope

### In Scope
1. Download resume for interrupted transfers
2. File integrity validation (images, audio)
3. DVC integration for dataset versioning
4. Git-LFS integration for large files
5. Multi-format export in single pass
6. Framework-specific export templates

### Out of Scope
- Full DVC pipeline automation (future)
- TensorFlow TFRecord export (future)
- Cloud storage backends (future)

---

## User Stories

| ID | Story | Points | Priority |
|----|-------|--------|----------|
| US-036 | Download Resume | 8 | Must Have |
| US-037 | File Integrity Checks | 5 | Must Have |
| US-038 | DVC Integration | 5 | Should Have |
| US-039 | Git-LFS Integration | 3 | Should Have |
| US-040 | Multi-Format Export | 3 | Could Have |
| US-041 | Framework Export Templates | 5 | Could Have |

**Total Points:** 29

---

## Dependencies

- US-036 depends on: FetchService (v0.1.0)
- US-037 depends on: Validation framework (v0.1.0)
- US-038 depends on: Manifest generation (v0.1.0)
- US-039 depends on: Export pipeline (v0.1.0)

---

## Testing Strategy

- Unit tests for resume logic
- Integration tests for DVC/LFS (mocked)
- E2E tests for file integrity checks

---

## Success Criteria

- Downloads can resume from interruption
- Invalid files are detected and reported
- DVC .dvc files generated correctly
- Git-LFS patterns configured properly

---

**End of Document**
