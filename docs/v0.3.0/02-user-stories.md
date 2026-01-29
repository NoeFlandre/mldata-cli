# mldata-cli v0.3.0 User Stories

## Story Format
```
As a [role]
I want to [capability]
So that [benefit]
```

---

## Theme 1: Performance (HIGH PRIORITY)

### US-001: Parallel Dataset Processing
```
As a data engineer
I want to process multiple files in parallel
So that large datasets build faster

Acceptance Criteria:
- [ ] Process up to 4 files concurrently
- [ ] Configurable worker count
- [ ] Progress bars for each worker
- [ ] Preserve output order
- [ ] Handle worker failures gracefully

Priority: MUST HAVE
Points: 8
```

### US-002: Incremental Builds
```
As a data engineer
I want to skip reprocessing unchanged files
So that I save time when only some data changes

Acceptance Criteria:
- [ ] Hash source files before processing
- [ ] Compare with previous build hash
- [ ] Skip unchanged files
- [ ] Rebuild only changed files
- [ ] Show skipped files in output

Priority: MUST HAVE
Points: 5
```

---

## Theme 2: Data Profiling (HIGH PRIORITY)

### US-003: Dataset Statistics
```
As a data scientist
I want to see statistical summary of my dataset
So that I understand data distribution before modeling

Acceptance Criteria:
- [ ] Show mean, std, min, max for numeric columns
- [ ] Show percentiles (25, 50, 75)
- [ ] Show value counts for categorical columns
- [ ] Show null counts and percentages
- [ ] Output in Rich table format

Priority: MUST HAVE
Points: 5
```

### US-004: Profile Command
```
As a data analyst
I want a dedicated profile command
So that I can analyze any dataset quickly

Acceptance Criteria:
- [ ] Command: `mldata profile <path>`
- [ ] Support all formats (CSV, Parquet, JSONL)
- [ ] Show schema information
- [ ] Show statistical summary
- [ ] Export profile to JSON

Priority: MUST HAVE
Points: 5
```

---

## Theme 3: Data Quality (MEDIUM PRIORITY)

### US-005: Data Drift Detection
```
As a ML engineer
I want to detect data drift between builds
So that I can identify distribution changes

Acceptance Criteria:
- [ ] Calculate Population Stability Index (PSI)
- [ ] Calculate KL Divergence
- [ ] Compare numeric distributions
- [ ] Compare categorical distributions
- [ ] Show drift warnings

Priority: SHOULD HAVE
Points: 8
```

### US-006: Schema Evolution Tracking
```
As a data engineer
I want to track schema changes across builds
So that I can catch breaking changes early

Acceptance Criteria:
- [ ] Store previous schema in manifest
- [ ] Detect new columns
- [ ] Detect removed columns
- [ ] Detect type changes
- [ ] Show schema diff

Priority: SHOULD HAVE
Points: 5
```

---

## Theme 4: Compression (MEDIUM PRIORITY)

### US-007: Configurable Compression
```
As a data engineer
I want to choose compression level
So that I can balance file size vs speed

Acceptance Criteria:
- [ ] Support snappy (fast, larger)
- [ ] Support gzip (medium)
- [ ] Support zstd (slow, smallest)
- [ ] Add --compression flag to build
- [ ] Document tradeoffs

Priority: SHOULD HAVE
Points: 3
```

---

## Theme 5: UX Improvements (MEDIUM PRIORITY)

### US-008: Build Cancellation
```
As a user
I want to cancel a running build with Ctrl+C
So that I can stop long-running operations

Acceptance Criteria:
- [ ] Catch KeyboardInterrupt
- [ ] Clean up partial files
- [ ] Show cancellation message
- [ ] Exit with code 130

Priority: SHOULD HAVE
Points: 3
```

### US-009: Configuration File
```
As a power user
I want to save default options in a config file
So that I don't have to specify them every time

Acceptance Criteria:
- [ ] Support YAML config file
- [ ] Set default format, split ratios
- [ ] Set default compression
- [ ] Per-project and global config
- [ ] Command: `mldata config`

Priority: COULD HAVE
Points: 5
```

### US-010: Better Progress Reporting
```
As a user
I want to see more informative progress bars
So that I know what's happening during long operations

Acceptance Criteria:
- [ ] Show ETA for long operations
- [ ] Show processing speed (MB/s)
- [ ] Show current operation (fetching, normalizing, splitting)
- [ ] Show files processed count

Priority: COULD HAVE
Points: 3
```

---

## Story Summary

| Story | Priority | Points | Theme |
|-------|----------|--------|-------|
| US-001 | MUST HAVE | 8 | Performance |
| US-002 | MUST HAVE | 5 | Performance |
| US-003 | MUST HAVE | 5 | Profiling |
| US-004 | MUST HAVE | 5 | Profiling |
| US-005 | SHOULD HAVE | 8 | Quality |
| US-006 | SHOULD HAVE | 5 | Quality |
| US-007 | SHOULD HAVE | 3 | Compression |
| US-008 | SHOULD HAVE | 3 | UX |
| US-009 | COULD HAVE | 5 | UX |
| US-010 | COULD HAVE | 3 | UX |

**Total Stories**: 10
**Total Points**: 50
