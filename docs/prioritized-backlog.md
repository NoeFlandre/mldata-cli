# mldata-cli — Prioritized Backlog

## Document Control

| Field | Value |
|-------|-------|
| **Version** | 1.0 |
| **Date** | 2026-01-29 |
| **Author** | Noé Flandre |
| **Status** | Draft |
| **Parent Document** | [User Story Backlog](./user-story-backlog.md) |

---

## Priority Definitions

| Priority | Definition | Release Target |
|----------|------------|----------------|
| **P0** | MVP-Critical: Core functionality required for initial release | v0.1.0 (MVP) |
| **P1** | MVP: Important features for initial release | v0.1.0 (MVP) |
| **P2** | Post-MVP: Valuable features for subsequent releases | v0.2.0+ |

## Effort Estimates

| Size | Story Points | Typical Duration | Complexity |
|------|--------------|------------------|------------|
| **S** | 1-2 | Few hours | Simple, well-defined |
| **M** | 3-5 | 1-2 days | Moderate complexity |
| **L** | 8-13 | 3-5 days | Complex, multiple components |
| **XL** | 21+ | 1-2 weeks | Very complex, significant unknowns |

---

## MVP Scope Summary

**MVP (v0.1.0) includes:**
- 3 connectors: HuggingFace, Kaggle, OpenML
- Core pipeline: search → pull → normalize → validate → split → export
- Manifest generation and rebuild
- Basic quality reports
- CLI foundation with Rich output

**Total MVP Story Points:** ~85 points
**Estimated Sprints:** 6 (2-week sprints)

---

## Prioritized Story List

### P0 — MVP-Critical (Must Have)

| Rank | Story | Epic | Effort | Dependencies | Risk | Sprint |
|------|-------|------|--------|--------------|------|--------|
| 1 | **US-005**: Download Dataset by URI | E2 | M | None | Low | 1 |
| 2 | **US-008**: Authentication Management | E2 | M | None | Medium | 1 |
| 3 | **US-001**: Unified Dataset Search | E1 | L | US-005, US-008 | Medium | 2 |
| 4 | **US-006**: Caching Downloaded Data | E2 | M | US-005 | Low | 2 |
| 5 | **US-011**: Automatic Format Detection | E3 | M | US-005 | Low | 2 |
| 6 | **US-022**: Basic Train/Val/Test Split | E5 | M | US-011 | Low | 3 |
| 7 | **US-024**: Deterministic Seeding | E5 | S | US-022 | Low | 3 |
| 8 | **US-034**: Manifest Generation | E7 | M | US-005, US-022 | Low | 3 |
| 9 | **US-026**: Parquet Export | E6 | M | US-011 | Low | 4 |
| 10 | **US-032**: Rebuild from Manifest | E7 | L | US-034 | Medium | 4 |
| 11 | **US-021**: Quality Report Generation | E4 | M | US-011 | Low | 4 |

**P0 Total:** 11 stories, ~45 points

---

### P1 — MVP (Should Have)

| Rank | Story | Epic | Effort | Dependencies | Risk | Sprint |
|------|-------|------|--------|--------------|------|--------|
| 12 | **US-003**: Dataset Information Display | E1 | M | US-005 | Low | 2 |
| 13 | **US-009**: Download Progress Reporting | E2 | S | US-005 | Low | 2 |
| 14 | **US-013**: Standardized Directory Layout | E3 | M | US-005 | Low | 3 |
| 15 | **US-012**: Format Conversion | E3 | M | US-011 | Low | 3 |
| 16 | **US-016**: Duplicate Detection | E4 | L | US-011 | Medium | 4 |
| 17 | **US-017**: Label Distribution Analysis | E4 | M | US-011 | Low | 4 |
| 18 | **US-018**: Missing Value Detection | E4 | S | US-011 | Low | 4 |
| 19 | **US-023**: Stratified Splitting | E5 | M | US-022 | Low | 5 |
| 20 | **US-025**: Split Index Files | E5 | S | US-022 | Low | 5 |
| 21 | **US-027**: JSONL Export | E6 | S | US-011 | Low | 5 |
| 22 | **US-033**: Build Verification | E7 | M | US-032 | Low | 5 |
| 23 | **US-014**: Schema Inference | E3 | M | US-011 | Low | 5 |
| 24 | **US-002**: Filter Search Results | E1 | M | US-001 | Low | 6 |
| 25 | **US-007**: Resume Interrupted Downloads | E2 | M | US-005 | Medium | 6 |
| 26 | **US-019**: Schema Validation | E4 | M | US-014 | Low | 6 |

**P1 Total:** 15 stories, ~40 points

---

### P2 — Post-MVP (Nice to Have)

| Rank | Story | Epic | Effort | Dependencies | Risk | Sprint |
|------|-------|------|--------|--------------|------|--------|
| 27 | **US-004**: Dataset Preview | E1 | M | US-003 | Low | 7 |
| 28 | **US-010**: Multi-file Dataset Handling | E2 | L | US-005 | Medium | 7 |
| 29 | **US-015**: Multimodal Data Handling | E3 | L | US-011 | Medium | 7 |
| 30 | **US-020**: File Integrity Checks | E4 | L | US-015 | Medium | 8 |
| 31 | **US-028**: Multiple Format Export | E6 | S | US-026, US-027 | Low | 7 |
| 32 | **US-029**: DVC Integration | E6 | M | US-026 | Medium | 8 |
| 33 | **US-030**: Git-LFS Integration | E6 | M | US-026 | Low | 8 |
| 34 | **US-031**: Framework-Specific Export | E6 | M | US-026 | Low | 9 |
| 35 | **US-035**: Dataset Diff | E7 | L | US-034 | Medium | 9 |

**P2 Total:** 9 stories, ~40 points

---

## Dependency Graph

```
                                    ┌─────────────┐
                                    │ US-005:     │
                                    │ Download    │
                                    │ by URI      │
                                    └──────┬──────┘
                                           │
              ┌────────────────────────────┼────────────────────────────┐
              │                            │                            │
              ▼                            ▼                            ▼
       ┌─────────────┐              ┌─────────────┐              ┌─────────────┐
       │ US-008:     │              │ US-006:     │              │ US-009:     │
       │ Auth        │              │ Caching     │              │ Progress    │
       └──────┬──────┘              └─────────────┘              └─────────────┘
              │
              ▼
       ┌─────────────┐              ┌─────────────┐
       │ US-001:     │              │ US-011:     │
       │ Search      │◄─────────────│ Format      │
       └──────┬──────┘              │ Detection   │
              │                     └──────┬──────┘
              ▼                            │
       ┌─────────────┐      ┌──────────────┼──────────────┬──────────────┐
       │ US-002:     │      │              │              │              │
       │ Filters     │      ▼              ▼              ▼              ▼
       └──────┬──────┘ ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐
              │        │ US-012: │   │ US-013: │   │ US-014: │   │ US-022: │
              ▼        │ Convert │   │ Layout  │   │ Schema  │   │ Split   │
       ┌─────────────┐ └─────────┘   └─────────┘   └────┬────┘   └────┬────┘
       │ US-003:     │                                  │              │
       │ Info        │                                  ▼              │
       └──────┬──────┘                            ┌─────────┐          │
              │                                   │ US-019: │          │
              ▼                                   │ Schema  │          │
       ┌─────────────┐                            │ Valid   │          │
       │ US-004:     │                            └─────────┘          │
       │ Preview     │                                                 │
       └─────────────┘                    ┌────────────────────────────┼────────────┐
                                          │                            │            │
                                          ▼                            ▼            ▼
                                   ┌─────────────┐              ┌─────────┐  ┌─────────┐
                                   │ US-023:     │              │ US-024: │  │ US-025: │
                                   │ Stratify    │              │ Seed    │  │ Indices │
                                   └─────────────┘              └────┬────┘  └─────────┘
                                                                     │
                                                                     ▼
                                                              ┌─────────────┐
                                                              │ US-034:     │
                                                              │ Manifest    │
                                                              └──────┬──────┘
                                                                     │
                                          ┌──────────────────────────┼──────────────┐
                                          │                          │              │
                                          ▼                          ▼              ▼
                                   ┌─────────────┐            ┌─────────┐    ┌─────────┐
                                   │ US-032:     │            │ US-033: │    │ US-035: │
                                   │ Rebuild     │            │ Verify  │    │ Diff    │
                                   └─────────────┘            └─────────┘    └─────────┘
```

---

## Risk Analysis

### High Risk Stories

| Story | Risk | Mitigation |
|-------|------|------------|
| US-001: Unified Search | API differences across sources | Abstract early, use adapter pattern |
| US-008: Auth Management | Keyring compatibility across OS | Test on Linux/macOS/Windows early |
| US-016: Duplicate Detection | Performance on large datasets | Use efficient algorithms (MinHash), add limits |
| US-010: Multi-file Datasets | Complex directory structures | Test with diverse real datasets |

### Medium Risk Stories

| Story | Risk | Mitigation |
|-------|------|------------|
| US-007: Resume Downloads | Not all sources support range requests | Graceful fallback to full download |
| US-015: Multimodal Handling | Many edge cases with media files | Start with common formats only |
| US-029: DVC Integration | External tool dependency | Clear error messages, optional feature |
| US-035: Dataset Diff | Complex comparison logic | Start with manifest diff only |

### Technical Debt Considerations

| Area | Debt Risk | Prevention |
|------|-----------|------------|
| Connector abstraction | Leaky abstractions | Strong interface contracts, regular refactoring |
| Error handling | Inconsistent errors | Centralized error types from day 1 |
| Testing | Low coverage | Enforce 80% coverage, VCR.py for APIs |
| Documentation | Outdated docs | Docs as code, update with PRs |

---

## Sprint Allocation Summary

| Sprint | Focus | Stories | Points |
|--------|-------|---------|--------|
| 1 | Foundation | US-005, US-008 | ~10 |
| 2 | Discovery & Cache | US-001, US-003, US-006, US-009, US-011 | ~18 |
| 3 | Normalization & Split | US-012, US-013, US-022, US-024, US-034 | ~15 |
| 4 | Validation & Export | US-016, US-017, US-018, US-021, US-026, US-032 | ~22 |
| 5 | Polish & Extend | US-014, US-019, US-023, US-025, US-027, US-033 | ~15 |
| 6 | Complete MVP | US-002, US-007 + bug fixes, polish | ~10 |

**Total MVP:** ~90 points across 6 sprints

---

## MVP Definition of Done

A story is complete when:

1. **Code Complete**
   - [ ] Implementation matches acceptance criteria
   - [ ] Code reviewed and approved
   - [ ] No known bugs

2. **Testing Complete**
   - [ ] Unit tests written (80% coverage)
   - [ ] Integration tests for external APIs (VCR.py)
   - [ ] Manual testing on Linux/macOS

3. **Documentation Complete**
   - [ ] CLI help text updated
   - [ ] User-facing changes documented
   - [ ] Technical notes for complex logic

4. **Ready for Release**
   - [ ] No breaking changes without version bump
   - [ ] Changelog entry added
   - [ ] CI passes

---

## Traceability

| Document | Traces From | Traces To |
|----------|-------------|-----------|
| Prioritized Backlog | User Story Backlog | Sprint Backlog |
| Stories | Epics, PRD | Implementation, Tests |
| Priority | Product Vision, KPIs | Release Plan |

---

**End of Document**
