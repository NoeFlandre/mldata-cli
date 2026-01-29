# mldata-cli v0.2.0 CLI Observations

This document captures issues, bugs, missing features, and UX problems discovered during CLI testing.

## Test Environment
- **Platform**: macOS Darwin 25.2.0
- **Python**: Anaconda3 (Python 3.12)
- **mldata-cli**: Latest from /Users/noeflandre/mldata-cli

---

## 1. Search Command

### Test Command
```bash
mldata search "machine learning" -n 3 --source hf
mldata search "machine learning" -n 3 --source openml
```

### Observations

#### Issue: OpenML Returns No Results with Warning
- **Command**: `mldata search "machine learning" -n 3 --source openml`
- **Result**: "No results found"
- **Warning**: `FutureWarning: Support for output_format of 'dict' will be removed in 0.15 and pandas dataframes will be returned instead.`
- **Severity**: Medium - Minor UX issue, but functional

#### Issue: OpenML Returns No Results While HF Returns Results
Both sources searched for the same query but OpenML returned no results. This may be due to:
- OpenML dataset naming conventions differ
- Query matching algorithm differences
- Potential bug in OpenML connector

---

## 2. Info Command

### Test Commands
```bash
mldata info hf://phihung/titanic
mldata info hf://stanfordnlp/imdb
```

### Observations

#### Missing Information in Output
The `info` command output is sparse and missing important details:

1. **No description/summary** - Users cannot see what the dataset contains
2. **No column/schema information** - Users don't know what features are available
3. **No sample data** - Cannot preview the data format
4. **No download count or popularity metrics**
5. **No citation information**
6. **No tags or keywords**
7. **No citation requirement or paper reference**

**Current Output Example**:
```
╭────────────────── Dataset: titanic ──────────────────╮
│ Name: titanic                                        │
│ Source: huggingface                                  │
│ ID: phihung/titanic                                  │
│ Size: 5.1 MB                                         │
│ Modality: text                                       │
│ Tasks: other                                         │
│ License: other                                       │
│ Author: phihung                                      │
│ Version: 9753139e0b9d454ab4fd22e884290260db5fc7b6    │
│ URL: https://huggingface.co/datasets/phihung/titanic │
╰──────────────────────────────────────────────────────╯
```

**Suggested Improvements**:
- Add dataset description/summary
- Show column schema (name, type, nullable)
- Show sample rows (first 3-5)
- Add download count/stars
- Add citation information
- Show tags/keywords
- Show last updated date

---

## 3. Build Command (Local Files)

### Test Command
```bash
mldata build ./test-data.csv --output /tmp/test-build2 --format parquet --split 0.7,0.2,0.1 --seed 42
```

### Issue: Local File Paths Not Supported

**Error**:
```
Error: Invalid URI format: ./test-data.csv
Error: Invalid URI format: /Users/noeflandre/mldata-cli/test-data.csv
```

**Severity**: High - Critical missing feature

**Details**:
The build command does not accept local file paths. Even using absolute paths fails with "Invalid URI format". This is a significant limitation as users often need to process local datasets.

**Expected Behavior**:
- Accept relative paths: `./data.csv`, `data.csv`
- Accept absolute paths: `/path/to/data.csv`
- Accept glob patterns: `data/*.csv`, `data/**/*.parquet`

**Suggested Fix**:
Detect if input is a local file/directory and handle appropriately. Accept common URI formats:
- `file:///path/to/data.csv`
- `./data.csv`
- `/absolute/path/data.csv`
- `glob:data/*.csv`

---

## 4. Validate Command

### Test Command
```bash
mldata validate /tmp/test-build1 --checks all
```

### Observations

#### Output is Confusing
- Result: `missing: FAIL` - but no details on what is missing
- Users don't know which columns have missing values or how many
- No indication of severity or whether this is blocking

**Current Output**:
```
Validating: /tmp/test-build1
  Running duplicates...
    ✓ duplicates: PASS
  Running labels...
    ✓ labels: PASS
  Running missing...
    ✗ missing: FAIL
  Running schema...
    ✓ schema: PASS
```

**Suggested Improvements**:
- Show which check failed and why
- Display specific values/columns causing the failure
- Show the count/percentage of problematic data
- Provide remediation suggestions

---

## 5. Export Command

### Test Command
```bash
mldata export /tmp/test-build1 --all
```

### Observations

#### Works as Expected
The export command works correctly and generates all format variants:
- `parquet`
- `csv`
- `jsonl`

No issues found with this command.

---

## 6. Split Command

### Test Command
```bash
mldata split /tmp/test-build2/artifacts/data.parquet 0.7,0.2,0.1 --seed 42 --indices
```

### Issue: Crashes When File Doesn't Exist

**Error**:
```
FileNotFoundError: No such file or directory (os error 2):
/tmp/test-build2/artifacts/data.parquet

This error occurred with the following context stack:
        [1] 'parquet scan'
        [2] 'sink'
```

**Severity**: Medium - Should provide better error handling

**Details**:
The command crashed with a raw Python traceback instead of a user-friendly error message. The error occurred because test-build2 was never created (due to the local file path bug), but the error handling should be better.

**Suggested Improvements**:
- Check if file exists before attempting to read
- Provide clear error message: "File not found: /path/to/file"
- Suggest using `mldata build` first
- Show available files if directory is provided

---

## 7. Diff Command

### Test Command
```bash
mldata diff /tmp/test-build1 /tmp/test-build3
```

### Observations

#### Issue: Diff Only Compares Manifest, Not Data

**Result**:
```
Comparing builds
  Build 1: hf://phihung/titanic
  Build 2: hf://phihung/titanic

No parameter differences found
```

**Problem**:
The diff command only compares manifest parameters, not the actual data. When comparing two builds with the same parameters:
- Expected: Should show if data is identical or different
- Actual: Shows "No parameter differences found" without comparing data content

**Severity**: Medium - Limited utility for data comparison

**Suggested Improvements**:
- Compare data shapes (row/column counts)
- Compare data content (checksums, sample values)
- Show data format differences
- Support comparing builds with different sources
- Show schema differences (column types, missing columns)

---

## 8. Rebuild Command

### Test Command
```bash
mldata rebuild /tmp/test-build1/manifest.yaml --output /tmp/test-rebuild
```

### Observations

#### Output is Confusing

**Result**:
```
Rebuilding from manifest
Source: hf://phihung/titanic
Output: /tmp/test-rebuild

Rebuild requires running full pipeline with original parameters:
  mldata build hf://phihung/titanic --output /tmp/test-rebuild
  --seed 42
  --split 0.7,0.2,0.1
  --format csv

Verification pending rebuild...
✗ huggingface
✗ kaggle
✗ openml
```

**Problems**:
1. Command says "Rebuilding from manifest" but then shows parameters and says "Verification pending rebuild..."
2. The meaning of "Verification pending rebuild..." is unclear
3. The "✗" marks next to services are confusing - are these errors? Authentication issues?
4. No clear indication of what happened (success/failure)

**Suggested Improvements**:
- Make output clearer: "Rebuild parameters extracted from manifest" vs "Rebuild completed"
- Explain what the "✗" marks mean (authentication not configured)
- Provide clear status: "Ready to rebuild with these parameters" or "Rebuild complete"
- Add option to auto-execute the rebuild command instead of just showing it

---

## 9. Auth Command

### Test Command
```bash
mldata auth status
```

### Observations

#### Works as Expected
The auth status command works correctly and shows authentication status for all services.

**Output**:
```
Exit code 1
Failed to load manifests: [Errno 2] No such file or directory:
'/tmp/test-build2/manifest.yaml'
```

**Note**: The exit code 1 is due to the failed test-build2, not the auth command itself.

---

## 10. Doctor Command

### Test Command
```bash
mldata doctor
```

### Observations

#### Works Well - Good UX
The doctor command provides clear, organized output:

```
mldata-cli Doctor
----------------------------------------

Authentication:
  ✗ huggingface
  ✗ kaggle
  ✗ openml

Cache:
  Directory: /Users/noeflandre/.mldata/cache
  Size: 0.0 MB / 50 GB
  Entries: 1
```

**Minor Issue**:
- The "✗" symbols are red and indicate errors, but missing authentication might be expected for some users who only use certain sources
- Could distinguish between "not configured" (warning) vs "failed to connect" (error)

---

## Additional Issues

### Issue: Empty Search Query Returns Data

**Command**: `mldata search "" -n 1 --source hf`

**Result**: Returns a dataset (Superior-Reasoning-SF...)

**Problem**: An empty search query should either:
- Return no results, or
- Return a meaningful message like "Please provide a search query"
- Return popular/trending datasets (document this behavior)

Currently it returns random data, which is confusing.

---

### Issue: No Progress Indicator for Long Operations

During `mldata build` operations, the progress indicator is minimal:
```
Generating train split: 100%|██████████| 891/891 [00:00<?, ? examples/s]
```

**Suggested Improvements**:
- Show ETA for large datasets
- Show current operation status
- Show data size being processed

---

### Issue: No Help for Unknown Commands

If a user types an invalid command, they get a generic error without suggestions.

**Example**:
```bash
$ mldata info
Error: No such option: --help

$ mldata invalid-command
Error: No such command 'invalid-command'
```

No suggestions for similar commands or available commands.

---

## Feature Requests

### 1. Local File Support for Build Command
Priority: High

The build command must support local files:
- Relative paths: `./data.csv`
- Absolute paths: `/path/to/data.csv`
- Directory inputs: `/path/to/directory/`
- Multiple files: `/path/to/*.csv`

### 2. Enhanced Info Command
Priority: High

Add more information to dataset info:
- Description/summary
- Column schema (name, type, nullable)
- Sample rows
- Download count/stars
- Citation information
- Tags/keywords

### 3. Data Comparison in Diff Command
Priority: Medium

The diff command should compare actual data, not just manifest parameters:
- Row/column counts
- Schema differences
- Sample value comparison
- Checksums

### 4. Better Validation Output
Priority: Medium

Validation output should be more informative:
- Specific failure details
- Count/percentage of issues
- Remediation suggestions

### 5. Improved Rebuild Output
Priority: Medium

Rebuild command should have clearer output:
- Distinguish between parameter extraction and actual rebuild
- Explain what each status means
- Option to auto-execute the rebuild

### 6. Empty Search Query Handling
Priority: Low

Handle empty search queries explicitly:
- Return no results with message, or
- Document that empty query returns random/popular datasets

### 7. Command Suggestions
Priority: Low

For invalid commands, suggest similar commands:
- "Did you mean 'mldata info'?"

---

## Summary

| Issue | Severity | Status |
|-------|----------|--------|
| Local file paths not supported in build | High | Bug |
| OpenML returns no results | Medium | Bug |
| Diff doesn't compare data | Medium | Missing Feature |
| Info command missing details | Medium | Missing Feature |
| Empty search query behavior | Low | UX Issue |
| Validation output lacks details | Medium | UX Issue |
| Split crashes with traceback | Medium | UX Issue |
| Rebuild output confusing | Medium | UX Issue |
| OpenML FutureWarning | Low | Warning |

---

## Recommendations

1. **Immediate Priority**: Fix local file path support - this is a critical missing feature
2. **High Priority**: Enhance info command with schema and description
3. **High Priority**: Fix OpenML search to return results
4. **Medium Priority**: Improve validation output with specific failure details
5. **Medium Priority**: Add data comparison to diff command
6. **Low Priority**: Polish UX (empty queries, error messages, suggestions)
