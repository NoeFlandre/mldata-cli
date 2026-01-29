# mldata-cli v0.2.0 Epic

## Release Overview
**Version**: v0.2.0
**Theme**: Local Data Support & Enhanced UX
**Release Date**: TBD
**Epic Lead**: Claude (AI Assistant)

---

## Problem Statement

Based on v0.1.0 user testing, critical gaps were identified:

1. **Local file paths not supported** - Users cannot process local CSV/Parquet files
2. **Info command is sparse** - Missing schema, descriptions, sample data
3. **Validation output unclear** - FAIL without actionable details
4. **Diff command limited** - Only compares manifests, not actual data
5. **OpenML connector broken** - Returns no results with FutureWarning
6. **Rebuild UX confusing** - Unclear what happened vs what will happen

---

## Goals

### Primary Goals
- [ ] Support local file paths in all commands (HIGH)
- [ ] Enhance info command with schema and samples (HIGH)
- [ ] Fix OpenML connector (HIGH)
- [ ] Improve validation output with details (MEDIUM)
- [ ] Add data comparison to diff (MEDIUM)

### Secondary Goals
- [ ] Improved error messages
- [ ] Better progress indicators
- [ ] Command suggestions for typos
- [ ] Enhanced rebuild functionality

---

## Scope

### In Scope
- Local file path handling (`./data.csv`, `/path/to/data.parquet`, `data/`)
- Enhanced `mldata info` with schema, samples, citations
- OpenML connector fix
- Validation output improvements
- Data comparison in `mldata diff`
- Rebuild command execution (not just parameter extraction)
- Better error handling and user feedback

### Out of Scope
- New data sources (focus on fixing existing)
- Advanced analytics
- Web UI
- Cloud integration

---

## Success Criteria

| Criteria | Target | Measurement |
|----------|--------|-------------|
| Local file support | 100% of commands | Test all path variations |
| Info command satisfaction | >90% | User survey |
| Validation clarity | Specific errors shown | Inspect output |
| OpenML search results | >10 per query | Count results |
| All tests passing | 100% | CI pipeline |

---

## Dependencies

1. OpenML API changes (dict → dataframe)
2. Polars schema introspection
3. None external (all internal fixes)

---

## Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| OpenML API breaking change | High | Fallback to dataframe parsing |
| Local path edge cases | Medium | Comprehensive test suite |
| Breaking existing behavior | Medium | Versioned CLI args |

---

## Timeline

| Phase | Duration | Focus |
|-------|----------|-------|
| Sprint 1 | 1 week | Local file support, OpenML fix |
| Sprint 2 | 1 week | Info enhancements, validation |
| Sprint 3 | 1 week | Diff improvements, rebuild |
| Sprint 4 | 1 week | Polish, tests, docs |

**Total Estimated: 4 weeks**
