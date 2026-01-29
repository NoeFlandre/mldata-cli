# mldata-cli v0.2.0 Sprint Backlog

## Sprint 1: Foundation
**Dates**: Week 1
**Focus**: Local file support + OpenML fix
**Status**: COMPLETED

### User Stories
| ID | Story | Points | Status |
|----|-------|--------|--------|
| US-001 | Local CSV Input | 5 | DONE |
| US-002 | Local Parquet Input | 3 | DONE |
| US-003 | Local Directory Input | 3 | DONE |
| US-007 | OpenML Search Fix | 3 | DONE |

### Technical Tasks
- [x] Implement local path detection in connectors
- [x] Create LocalConnector class
- [x] Update build command to accept local paths
- [x] Add glob pattern support
- [x] Fix OpenML API calls (dict → dataframe)
- [x] Add unit tests for local file handling

### Definition of Done
- [x] All local path formats work (file://, /path, ./path, glob)
- [x] OpenML search returns results (using dataframe API)
- [x] No FutureWarnings (using output_format='dataframe')
- [x] 61 unit tests pass (+10 new tests)
- [x] CLI integration tested (build command works with local files)

---

## Sprint 2: Info + Validation
**Dates**: Week 2
**Focus**: Enhanced info command + validation improvements
**Status**: COMPLETED

### User Stories
| ID | Story | Points | Status |
|----|-------|--------|--------|
| US-004 | Schema Display | 5 | DONE |
| US-005 | Description & Citations | 3 | DONE |
| US-006 | Sample Preview | 2 | DONE |
| US-009 | Detailed Validation | 5 | DONE |

### Technical Tasks
- [x] Extend DatasetMetadata with schema field
- [x] Add schema extraction from Parquet/CSV
- [x] Update info command to show schema
- [x] Add citation extraction from HF API
- [x] Add sample data fetching
- [x] Update validation output with details
- [x] Add column-level validation results
- [x] Add remediation suggestions

### Definition of Done
- [x] Info shows schema table
- [x] Info shows sample rows
- [x] Validation shows specific failures
- [x] Remediation suggestions displayed
- [x] All tests pass (61 tests)

---

## Sprint 3: Diff + Rebuild
**Dates**: Week 3
**Focus**: Data comparison + rebuild execution
**Status**: COMPLETED

### User Stories
| ID | Story | Points | Status |
|----|-------|--------|--------|
| US-011 | Data Comparison | 5 | DONE |
| US-012 | Diff Reports | 2 | DONE |
| US-013 | Rebuild Execution | 5 | DONE |
| US-014 | Rebuild Modifications | 2 | DONE |

### Technical Tasks
- [x] Add data shape comparison to diff
- [x] Add schema comparison to diff
- [x] Add checksum comparison
- [x] Implement diff report export (detailed output)
- [x] Implement actual rebuild execution
- [x] Add verification step to rebuild
- [x] Add dry-run option for rebuild

### Definition of Done
- [x] Diff compares actual data
- [x] Diff shows row/column differences
- [x] Rebuild actually executes
- [x] Verification reports match
- [x] All tests pass (61 tests)

---

## Sprint 4: Polish
**Dates**: Week 4
**Focus**: UX improvements + documentation
**Status**: COMPLETED

### User Stories
| ID | Story | Points | Status |
|----|-------|--------|--------|
| US-010 | Validation Reports | 3 | DONE |
| US-015 | Error Messages | 3 | DONE |
| US-016 | Command Suggestions | 2 | DONE |
| US-017 | Progress Improvements | 3 | DONE |

### Technical Tasks
- [x] Add JSON/Markdown export for validation
- [x] Improve error message formatting
- [x] Add command suggestion infrastructure
- [x] Improve progress bar display (built-in to build commands)
- [x] Final testing and bug fixes

### Definition of Done
- [x] Reports export correctly (JSON and Markdown)
- [x] Error messages are helpful (contextual tips added)
- [x] All tests pass (61 tests)

---

## Sprint Capacity

| Sprint | Points | Buffer | Notes |
|--------|--------|--------|-------|
| 1 | 14 | 20% | Foundation work |
| 2 | 15 | 20% | Core features |
| 3 | 14 | 20% | Advanced features |
| 4 | 11 | 30% | Polish + buffer |

**Total Points**: 54
**With Buffer**: ~65

---

## Dependencies Between Sprints

```
Sprint 1 (Foundation)
    ↓
Sprint 2 (Info + Validation)  ← Depends on S1
    ↓
Sprint 3 (Diff + Rebuild)     ← Depends on S2
    ↓
Sprint 4 (Polish)             ← Depends on S1-S3
```

---

## Risk Mitigation

| Risk | Sprint | Impact | Mitigation |
|------|--------|--------|------------|
| OpenML API breaking | S1 | High | Fallback to dataframe parsing |
| Complex schema extraction | S2 | Medium | Use Polars built-in methods |
| Rebuild verification | S3 | Medium | Hash comparison only |
| Performance with large files | All | Medium | Lazy loading, streaming |

---

## Quality Gates

- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] Type checking passes (mypy)
- [ ] Linting passes (ruff)
- [ ] No new security vulnerabilities
- [ ] Documentation updated
- [ ] User stories verified
