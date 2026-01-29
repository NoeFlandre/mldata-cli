# mldata-cli v0.3.0 Sprint Backlog

## Sprint 1: Performance & Profiling
**Dates**: Week 1
**Focus**: Parallel processing + data profiling

### User Stories
| ID | Story | Points | Status |
|----|-------|--------|--------|
| US-001 | Parallel Dataset Processing | 8 | TODO |
| US-002 | Incremental Builds | 5 | TODO |
| US-003 | Dataset Statistics | 5 | TODO |
| US-004 | Profile Command | 5 | TODO |

### Technical Tasks
- [ ] Add parallel processing to build pipeline
- [ ] Implement file hashing for change detection
- [ ] Add incremental build logic
- [ ] Create statistics calculation functions
- [ ] Implement `mldata profile` command
- [ ] Add unit tests for profiling

### Definition of Done
- [ ] Parallel processing works (2-4x speedup)
- [ ] Incremental builds skip unchanged files
- [ ] Profile command shows statistics
- [ ] All tests pass

---

## Sprint 2: Compression & Incremental
**Dates**: Week 2
**Focus**: Compression options + incremental build polish

### User Stories
| ID | Story | Points | Status |
|----|-------|--------|--------|
| US-002 | Incremental Builds (cont.) | 5 | TODO |
| US-007 | Configurable Compression | 3 | TODO |

### Technical Tasks
- [ ] Implement zstd compression support
- [ ] Add compression level options
- [ ] Test compression tradeoffs (speed vs size)
- [ ] Update build command with compression flag
- [ ] Polish incremental build output

### Definition of Done
- [ ] Three compression options work
- [ ] Documentation of tradeoffs
- [ ] All tests pass

---

## Sprint 3: Drift Detection
**Dates**: Week 3
**Focus**: Data drift detection + schema evolution

### User Stories
| ID | Story | Points | Status |
|----|-------|--------|--------|
| US-005 | Data Drift Detection | 8 | TODO |
| US-006 | Schema Evolution Tracking | 5 | TODO |

### Technical Tasks
- [ ] Implement PSI (Population Stability Index) calculation
- [ ] Implement KL Divergence calculation
- [ ] Add numeric distribution comparison
- [ ] Add categorical distribution comparison
- [ ] Implement schema versioning in manifest
- [ ] Create schema diff output

### Definition of Done
- [ ] Drift metrics calculated correctly
- [ ] Schema changes detected
- [ ] All tests pass

---

## Sprint 4: Polish & UX
**Dates**: Week 4
**Focus**: Build cancellation, config, progress

### User Stories
| ID | Story | Points | Status |
|----|-------|--------|--------|
| US-008 | Build Cancellation | 3 | TODO |
| US-009 | Configuration File | 5 | TODO |
| US-010 | Better Progress Reporting | 3 | TODO |

### Technical Tasks
- [ ] Implement KeyboardInterrupt handling
- [ ] Add cleanup for partial files
- [ ] Create config file support (YAML)
- [ ] Add global and project config
- [ ] Enhance progress bars with ETA
- [ ] Final testing and bug fixes

### Definition of Done
- [ ] Build cancellation works
- [ ] Config file works
- [ ] Progress bars show ETA
- [ ] All tests pass
- [ ] Code coverage >80%

---

## Sprint Capacity

| Sprint | Points | Buffer | Notes |
|--------|--------|--------|-------|
| 1 | 23 | 20% | Core features |
| 2 | 8 | 20% | Smaller sprint |
| 3 | 13 | 20% | Complex features |
| 4 | 11 | 30% | Polish + buffer |

**Total Points**: 55
**With Buffer**: ~66

---

## Dependencies Between Sprints

```
Sprint 1 (Performance + Profiling)
    ↓
Sprint 2 (Compression + Polish)  ← Depends on S1
    ↓
Sprint 3 (Drift Detection)       ← Independent
    ↓
Sprint 4 (UX + Polish)           ← Depends on S1-S3
```

---

## Risk Mitigation

| Risk | Sprint | Impact | Mitigation |
|------|--------|--------|------------|
| Memory issues with parallel | S1 | Medium | Limit concurrency, streaming |
| Complex drift math | S3 | Medium | Use standard formulas |
| Config file parsing | S4 | Low | PyYAML is reliable |

---

## Quality Gates

- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] Type checking passes (mypy)
- [ ] Linting passes (ruff)
- [ ] No new security vulnerabilities
- [ ] Documentation updated
- [ ] User stories verified
