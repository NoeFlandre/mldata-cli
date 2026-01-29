# mldata-cli v0.2.0 User Stories

## Story Format
```
As a [role]
I want to [capability]
So that [benefit]
```

---

## Theme 1: Local File Support (HIGH PRIORITY)

### US-001: Local CSV File Input
```
As a data scientist
I want to process local CSV files with mldata build
So that I can prepare my own datasets for ML

Acceptance Criteria:
- [ ] Accept relative paths: `./data.csv`, `data.csv`
- [ ] Accept absolute paths: `/path/to/data.csv`
- [ ] Accept directory inputs: `/path/to/directory/`
- [ ] Detect format automatically from extension
- [ ] Show clear error if file not found
- [ ] Support multiple files with glob patterns: `data/*.csv`

Priority: MUST HAVE
Points: 5
```

### US-002: Local Parquet File Input
```
As a data engineer
I want to process local Parquet files
So that I can work with columnar data formats

Acceptance Criteria:
- [ ] Accept `.parquet` files
- [ ] Read schema from Parquet metadata
- [ ] Preserve all column types
- [ ] Support partitioned Parquet directories

Priority: MUST HAVE
Points: 3
```

### US-003: Local Directory Input
```
As a ML engineer
I want to process a directory of mixed files
So that I can build datasets from existing data folders

Acceptance Criteria:
- [ ] Accept directory path
- [ ] Recursively find all supported files
- [ ] Show found files before processing
- [ ] Allow filtering by extension

Priority: SHOULD HAVE
Points: 3
```

---

## Theme 2: Enhanced Info Command (HIGH PRIORITY)

### US-004: Dataset Schema Display
```
As a data scientist
I want to see the column schema before downloading
So that I can understand what features are available

Acceptance Criteria:
- [ ] Show column names
- [ ] Show data types (string, int, float, bool)
- [ ] Show nullable status
- [ ] Show sample values
- [ ] Display in Rich table format

Priority: MUST HAVE
Points: 5
```

### US-005: Dataset Description & Citations
```
As a researcher
I want to see dataset descriptions and citations
So that I can properly cite the data source

Acceptance Criteria:
- [ ] Show dataset description/summary
- [ ] Show citation information
- [ ] Show paper reference if available
- [ ] Show license with link to full text
- [ ] Show author contact if available

Priority: SHOULD HAVE
Points: 3
```

### US-006: Sample Data Preview
```
As a data analyst
I want to preview sample rows before downloading
So that I can verify the data format

Acceptance Criteria:
- [ ] Show first 5 rows
- [ ] Truncate long text columns
- [ ] Handle nested structures
- [ ] Work with all supported sources

Priority: SHOULD HAVE
Points: 2
```

---

## Theme 3: OpenML Connector Fix (HIGH PRIORITY)

### US-007: OpenML Search Returns Results
```
As a researcher
I want to search OpenML datasets
So that I can find scientific datasets

Acceptance Criteria:
- [ ] Search returns actual results
- [ ] No FutureWarnings in output
- [ ] Results include dataset ID, name, size
- [ ] Support filtering by type

Priority: MUST HAVE
Points: 3
```

### US-008: OpenML Metadata Extraction
```
As a ML practitioner
I want to get full OpenML dataset metadata
So that I can understand dataset characteristics

Acceptance Criteria:
- [ ] Extract feature types
- [ ] Show target variables
- [ ] Display number of instances
- [ ] Show default split information

Priority: SHOULD HAVE
Points: 2
```

---

## Theme 4: Validation Improvements (MEDIUM PRIORITY)

### US-009: Detailed Validation Output
```
As a data engineer
I want clear validation failure details
So that I know exactly what to fix

Acceptance Criteria:
- [ ] Show which columns failed
- [ ] Show count/percentage of issues
- [ ] Show example problematic values
- [ ] Provide remediation suggestions
- [ ] Color-coded severity (warning vs error)

Priority: MUST HAVE
Points: 5
```

### US-010: Validation Report Export
```
As a quality analyst
I want to export validation reports
So that I can share findings with the team

Acceptance Criteria:
- [ ] Export to JSON format
- [ ] Export to Markdown format
- [ ] Include check details
- [ ] Include remediation steps

Priority: SHOULD HAVE
Points: 3
```

---

## Theme 5: Diff Command Enhancement (MEDIUM PRIORITY)

### US-011: Data Content Comparison
```
As a data scientist
I want to compare actual data between builds
So that I can verify data consistency

Acceptance Criteria:
- [ ] Compare row counts
- [ ] Compare column counts
- [ ] Compare schema (types, names)
- [ ] Show checksum differences
- [ ] Highlight data drift if present

Priority: SHOULD HAVE
Points: 5
```

### US-012: Diff Report Generation
```
As a QA engineer
I want to generate diff reports
So that I can document data changes

Acceptance Criteria:
- [ ] Export to JSON
- [ ] Export to Markdown
- [ ] Include visual diffs
- [ ] Include summary statistics

Priority: COULD HAVE
Points: 2
```

---

## Theme 6: Rebuild Improvements (MEDIUM PRIORITY)

### US-013: Rebuild Execution
```
As a ML engineer
I want to actually rebuild from manifest
So that I can reproduce my data pipeline

Acceptance Criteria:
- [ ] Execute rebuild (not just show commands)
- [ ] Use original source URI
- [ ] Apply original parameters (seed, split, format)
- [ ] Verify output matches manifest
- [ ] Report verification status

Priority: SHOULD HAVE
Points: 5
```

### US-014: Rebuild with Modifications
```
As a data scientist
I want to rebuild with modified parameters
So that I can experiment with different splits

Acceptance Criteria:
- [ ] Allow overriding seed
- [ ] Allow overriding split ratios
- [ ] Allow overriding format
- [ ] Show both original and modified parameters

Priority: COULD HAVE
Points: 2
```

---

## Theme 7: UX Improvements (LOW PRIORITY)

### US-015: Better Error Messages
```
As a new user
I want clear error messages with suggestions
So that I can fix issues without guessing

Acceptance Criteria:
- [ ] Show what went wrong
- [ ] Suggest how to fix
- [ ] Show relevant command examples
- [ ] Link to documentation

Priority: SHOULD HAVE
Points: 3
```

### US-016: Command Suggestions
```
As a forgetful user
I want suggestions for typos
So that I can find the right command

Acceptance Criteria:
- [ ] Suggest similar commands for typos
- [ ] Show available commands
- [ ] Fuzzy matching for command names

Priority: COULD HAVE
Points: 2
```

### US-017: Progress Improvements
```
As a user processing large datasets
I want better progress indicators
So that I know what's happening

Acceptance Criteria:
- [ ] Show ETA for long operations
- [ ] Show current operation
- [ ] Show data size processed
- [ ] Support multiple concurrent downloads

Priority: COULD HAVE
Points: 3
```

---

## Story Summary

| Story | Priority | Points | Theme |
|-------|----------|--------|-------|
| US-001 | MUST HAVE | 5 | Local Files |
| US-002 | MUST HAVE | 3 | Local Files |
| US-003 | SHOULD HAVE | 3 | Local Files |
| US-004 | MUST HAVE | 5 | Info |
| US-005 | SHOULD HAVE | 3 | Info |
| US-006 | SHOULD HAVE | 2 | Info |
| US-007 | MUST HAVE | 3 | OpenML |
| US-008 | SHOULD HAVE | 2 | OpenML |
| US-009 | MUST HAVE | 5 | Validation |
| US-010 | SHOULD HAVE | 3 | Validation |
| US-011 | SHOULD HAVE | 5 | Diff |
| US-012 | COULD HAVE | 2 | Diff |
| US-013 | SHOULD HAVE | 5 | Rebuild |
| US-014 | COULD HAVE | 2 | Rebuild |
| US-015 | SHOULD HAVE | 3 | UX |
| US-016 | COULD HAVE | 2 | UX |
| US-017 | COULD HAVE | 3 | UX |

**Total Stories**: 17
**Total Points**: 60
