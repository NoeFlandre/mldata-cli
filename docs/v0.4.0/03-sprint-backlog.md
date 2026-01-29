# mldata-cli v0.4.0 Sprint Backlog

## Document Control

| Field | Value |
|-------|-------|
| **Version** | 0.4.0 |
| **Date** | 2026-01-29 |
| **Author** | Noé Flandre |
| **Status** | Draft |
| **Parent Document** | [02-user-stories.md](./02-user-stories.md) |

---

## Sprint 1: Download Reliability
**Dates**: Week 1
**Focus**: Download resume and file integrity

### User Stories
| ID | Story | Points | Status |
|----|-------|--------|--------|
| US-036 | Download Resume | 8 | TODO |
| US-037 | File Integrity Checks | 5 | TODO |

### Technical Tasks
- [ ] Implement partial download detection
- [ ] Add range request support to FetchService
- [ ] Create resume logic with ETag/Last-Modified tracking
- [ ] Add image validation (PIL-based)
- [ ] Add audio validation (audiofile/ mutagen)
- [ ] Create `validate --checks files` command
- [ ] Add unit tests for resume logic
- [ ] Add unit tests for file validation

### Definition of Done
- [ ] Downloads resume from interruption
- [ ] Invalid files detected and reported
- [ ] All tests pass
- [ ] Documentation updated

---

## Sprint 2: Versioning Integration
**Dates**: Week 2
**Focus**: DVC and Git-LFS integration

### User Stories
| ID | Story | Points | Status |
|----|-------|--------|--------|
| US-038 | DVC Integration | 5 | TODO |
| US-039 | Git-LFS Integration | 3 | TODO |

### Technical Tasks
- [ ] Create DVC export functionality
- [ ] Generate .dvc files with proper structure
- [ ] Integrate manifest hashes with DVC
- [ ] Add Git-LFS pattern detection
- [ ] Auto-update .gitattributes
- [ ] Add --dvc and --git-lfs flags to export
- [ ] Add unit tests for DVC/LFS

### Definition of Done
- [ ] DVC integration works
- [ ] Git-LFS integration works
- [ ] All tests pass
- [ ] Documentation updated

---

## Sprint 3: Export Enhancements
**Dates**: Week 3
**Focus**: Multi-format export and framework templates

### User Stories
| ID | Story | Points | Status |
|----|-------|--------|--------|
| US-040 | Multi-Format Export | 3 | TODO |
| US-041 | Framework Export Templates | 5 | TODO |

### Technical Tasks
- [ ] Implement single-pass multi-format export
- [ ] Add --formats comma-separated flag
- [ ] Create PyTorch export template
- [ ] Generate loader code snippet
- [ ] Create README template with examples
- [ ] Add unit tests for export

### Definition of Done
- [ ] Multi-format export works
- [ ] Framework templates generated
- [ ] All tests pass
- [ ] Documentation updated

---

## Sprint Capacity

| Sprint | Points | Buffer | Notes |
|--------|--------|--------|-------|
| 1 | 13 | 20% | Core reliability |
| 2 | 8 | 20% | Integration features |
| 3 | 8 | 20% | Export enhancements |

**Total Points**: 29
**With Buffer**: ~35

---

## Dependencies Between Sprints

```
Sprint 1 (Download Reliability)
    ↓
Sprint 2 (Versioning Integration)  ← Independent
    ↓
Sprint 3 (Export Enhancements)    ← Depends on S2 (manifest)
```

---

## Risk Mitigation

| Risk | Sprint | Impact | Mitigation |
|------|--------|--------|------------|
| DVC API changes | S2 | Medium | Use stable features |
| PIL/mutagen deps | S1 | Low | Optional imports |
| Large file handling | S3 | Medium | Streaming |

---

## Quality Gates

- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] Type checking passes (mypy)
- [ ] Linting passes (ruff)
- [ ] No new security vulnerabilities
- [ ] Documentation updated
- [ ] User stories verified

---

**End of Document**
