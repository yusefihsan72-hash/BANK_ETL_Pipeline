# Phase 02 Implementation Execution Guide

## 1. Phase Goal

Build a production-ready **CSV extraction layer** that:
- Watches `data/incoming/` for new `{YYMMDD}_Customer.csv` and `{YYMMDD}_Transactions.csv` files
- Validates filename patterns, encoding, delimiter, and column schema before extraction
- Reads valid CSV files into `pandas.DataFrame` objects with extraction metadata
- Tracks processed files (by path + SHA-256 hash) to prevent reprocessing
- Quarantines files that fail validation with structured error records
- Provides config-driven **DB** and **API** extractor stubs (disabled by default, ready for future activation)
- Hands off `ExtractionResult` objects to the downstream transformation stage

---

## 2. Required Inputs

| Input | Location | Status |
|---|---|---|
| Python 3.10+ virtual environment | `.venv/` | Must be created |
| Core dependencies installed | `requirements.txt` | `pandas`, `pyyaml` minimum |
| Pipeline configuration | `config/config.yaml` | ✅ Exists from Phase 1 |
| Sample CSV files | `data/sample/` | ✅ Headers-only stubs exist |
| Incoming directory | `data/incoming/` | ✅ Created in Phase 1 |
| Processed directory | `data/processed/` | ✅ Created in Phase 1 |
| Quarantine directory | `quarantine/` | ✅ Created in Phase 1 |
| Logging initializer | `logging_config.py` | ✅ Exists from Phase 1 |
| Extraction package | `extraction/__init__.py` | ✅ Placeholder exists |

---

## 3. Execution Steps (Step-by-Step)

---

### Step 1 — Prepare Extraction Module Structure

**Purpose:** Create all module files inside `extraction/` so imports resolve cleanly.

**Files to create:**

| File | Role |
|---|---|
| `extraction/schema.py` | Expected column definitions + filename regex patterns |
| `extraction/csv_extractor.py` | Core CSV reading, validation, and directory-watch logic |
| `extraction/processed_tracker.py` | JSON-based deduplication tracker |
| `extraction/db_extractor.py` | Config-driven DB connector stub |
| `extraction/api_extractor.py` | Config-driven API connector stub |
| `config/config_loader.py` | YAML config loading utility |

**Files to modify:**

| File | Change |
|---|---|
| `extraction/__init__.py` | Re-export public API (`extract_csv_file`, `ExtractionResult`, etc.) |

**Implementation:**
1. Create each file with proper module docstring and imports.
2. Update `extraction/__init__.py` to expose the public surface:
   ```python
   from extraction.csv_extractor import extract_csv_file, watch_directory, ExtractionResult
   from extraction.schema import CUSTOMER_COLUMNS, TRANSACTION_COLUMNS, FILE_PATTERNS
   ```

---

### Step 2 — Implement Configuration Loader

**Purpose:** Provide a single reusable function for loading `config/config.yaml`.

**File:** [config/config_loader.py](file:///d:/BANK_ETL_Pipeline/config/config_loader.py) `[NEW]`

**Implementation:**
```python
import yaml
from pathlib import Path

_DEFAULT_CONFIG_PATH = Path(__file__).resolve().parent / "config.yaml"

def load_config(path: str | Path | None = None) -> dict:
    """Load and return the pipeline configuration dictionary."""
    config_path = Path(path) if path else _DEFAULT_CONFIG_PATH
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)
```

**Expected output:** Calling `load_config()` returns the full config dict with keys `watcher`, `sources`, `logging`, `warehouse`.

---

### Step 3 — Define Expected Schemas

**Purpose:** Centralized column definitions and filename patterns used by all extraction validation.

**File:** [extraction/schema.py](file:///d:/BANK_ETL_Pipeline/extraction/schema.py) `[NEW]`

**Implementation:**
```python
CUSTOMER_COLUMNS = [
    "customer_id", "age", "sex", "region", "income", "married",
    "children", "car", "save_act", "current_act", "mortgage", "pep",
]

TRANSACTION_COLUMNS = [
    "transaction_id", "customer_id", "date", "transaction_type",
    "amount", "balance", "description",
]

# Maps logical file type → regex for filename validation
FILE_PATTERNS = {
    "customer": r"^\d{6}_Customer\.csv$",
    "transaction": r"^\d{6}_Transactions\.csv$",
}

def get_expected_columns(file_type: str) -> list[str]:
    """Return the expected column list for the given file type."""
    mapping = {
        "customer": CUSTOMER_COLUMNS,
        "transaction": TRANSACTION_COLUMNS,
    }
    return mapping.get(file_type, [])
```

**Expected output:** Importable constants and a helper for column lookup.

---

### Step 4 — Implement Processed-File Tracker

**Purpose:** Prevent reprocessing of files across pipeline restarts using a JSON-persisted hash registry.

**File:** [extraction/processed_tracker.py](file:///d:/BANK_ETL_Pipeline/extraction/processed_tracker.py) `[NEW]`

**Implementation instructions:**
1. Track files by **absolute path → SHA-256 hash + timestamp**.
2. Persist to `data/processed/processed_files.json`.
3. Expose three public functions:

| Function | Signature | Behavior |
|---|---|---|
| `file_hash` | `(path: Path) → str` | Compute SHA-256 of the file in 8 KB chunks |
| `is_processed` | `(path: Path) → bool` | `True` if the file's current hash matches the stored hash |
| `mark_processed` | `(path: Path, hash_val: str) → None` | Record path, hash, and UTC timestamp |

4. If file exists in tracker but hash differs → return `False` from `is_processed` (file changed, needs reprocessing).
5. Create parent directories on first write.

**Key logic:**
```python
def is_processed(path: Path) -> bool:
    tracker = _load_tracker()
    entry = tracker.get(str(path.resolve()))
    if entry is None:
        return False
    # If hash changed, file must be re-extracted
    return entry["hash"] == file_hash(path)
```

**Expected output:** Calling `is_processed()` before and after `mark_processed()` returns `False` then `True`. A JSON file appears at `data/processed/processed_files.json`.

---

### Step 5 — Implement CSV Extractor

**Purpose:** Core extraction function that validates and reads a single CSV file into a DataFrame with metadata.

**File:** [extraction/csv_extractor.py](file:///d:/BANK_ETL_Pipeline/extraction/csv_extractor.py) `[NEW]`

**Implementation instructions:**

1. **Define `ExtractionResult` dataclass:**
   ```python
   @dataclass
   class ExtractionResult:
       source: str           # "customer" or "transaction"
       file_path: Path
       df: pd.DataFrame
       metadata: dict        # record_count, duration, hash, etc.
   ```

2. **Implement `classify_file(filename: str) → str | None`:**
   - Match filename against each pattern in `FILE_PATTERNS`.
   - Return the file type key (`"customer"` or `"transaction"`) or `None` if no match.

3. **Implement `extract_csv_file(file_path: Path, config: dict) → ExtractionResult | None`:**
   The function must follow this exact sequence:
   
   ```
   a. Start perf timer
   b. Classify file by name → reject if unknown pattern
   c. Check processed_tracker → skip if already processed (same hash)
   d. Read CSV with config-driven encoding/delimiter/quotechar
   e. On UnicodeDecodeError → retry with fallback encodings [utf-8-sig, latin1]
   f. Validate columns against schema → raise ValueError if missing required columns
   g. Compute file hash
   h. Mark file as processed
   i. Build metadata dict (file_name, record_count, duration_seconds, file_hash)
   j. Return ExtractionResult
   ```

4. **On any exception:** log the error and call the quarantine recorder (Step 8) before re-raising.

**Expected output:** Given a valid `240101_Customer.csv` in `data/incoming/`, returns an `ExtractionResult` with a DataFrame containing all 12 customer columns.

---

### Step 6 — Implement File Watcher / Directory Scanner

**Purpose:** Continuously (or on-demand) scan `data/incoming/` for new CSV files and feed them to `extract_csv_file`.

**File:** [extraction/csv_extractor.py](file:///d:/BANK_ETL_Pipeline/extraction/csv_extractor.py) (append to same file)

**Implementation instructions:**

1. **Implement `_is_file_stable(path: Path, wait: float = 1.5) → bool`:**
   - Read file size, sleep `wait` seconds, read again.
   - Return `True` only if size is unchanged (file is not being written).

2. **Implement `scan_incoming(config: dict) → list[ExtractionResult]`:**
   - Non-blocking single-pass scan of `data_dir` for `*.csv`.
   - Skip unstable files with a warning log.
   - Collect and return all `ExtractionResult` objects.
   - Catch per-file exceptions so one bad file doesn't abort the batch.

3. **Implement `watch_directory(config: dict) → None`:**
   - Infinite loop calling `scan_incoming()` then sleeping `polling_interval_seconds`.
   - Log each scan cycle (files found, files processed, files skipped).
   - Intended for long-running daemon mode; `scan_incoming` is for CLI / test use.

**Expected output:** Dropping a CSV into `data/incoming/` triggers extraction within the configured polling interval.

---

### Step 7 — Implement DB Extractor Stub

**Purpose:** Config-driven placeholder so future database extraction requires only enabling the config flag and filling connection details.

**File:** [extraction/db_extractor.py](file:///d:/BANK_ETL_Pipeline/extraction/db_extractor.py) `[NEW]`

**Implementation:**
```python
import logging
import pandas as pd

logger = logging.getLogger(__name__)

def extract_db(config: dict) -> pd.DataFrame | None:
    """
    Database extraction stub.
    Returns None when database source is disabled in config.
    TODO: Implement real DB extraction in a future phase.
    """
    db_config = config.get("sources", {}).get("database", {})
    if not db_config.get("enabled", False):
        logger.info("DB extractor is disabled in configuration — skipping.")
        return None

    # TODO: Connect using config["sources"]["database"]["connection_string"]
    # TODO: Execute query and return DataFrame
    logger.warning("DB extractor is enabled but not yet implemented.")
    return pd.DataFrame()
```

**Expected output:** Returns `None` when `sources.database.enabled` is `false` (current default).

---

### Step 8 — Implement API Extractor Stub

**Purpose:** Config-driven placeholder for REST API data sources with pagination skeleton.

**File:** [extraction/api_extractor.py](file:///d:/BANK_ETL_Pipeline/extraction/api_extractor.py) `[NEW]`

**Implementation:**
```python
import logging
import pandas as pd

logger = logging.getLogger(__name__)

def extract_api(config: dict) -> pd.DataFrame | None:
    """
    API extraction stub with pagination skeleton.
    Returns None when API source is disabled in config.
    TODO: Implement real API extraction in a future phase.
    """
    api_config = config.get("sources", {}).get("api", {})
    if not api_config.get("enabled", False):
        logger.info("API extractor is disabled in configuration — skipping.")
        return None

    # TODO: Implement real API call
    # base_url = api_config["base_url"]
    # auth_type = api_config["auth_type"]
    # pages = []
    # for page in range(1, max_pages + 1):
    #     response = requests.get(f"{base_url}?page={page}", ...)
    #     pages.append(pd.DataFrame(response.json()))
    # return pd.concat(pages, ignore_index=True)

    logger.warning("API extractor is enabled but not yet implemented.")
    return pd.DataFrame()
```

**Expected output:** Returns `None` when `sources.api.enabled` is `false`.

---

### Step 9 — Implement Error Handling & Quarantine Recorder

**Purpose:** Persist structured error records for files that fail extraction, enabling root-cause analysis.

**File:** [extraction/csv_extractor.py](file:///d:/BANK_ETL_Pipeline/extraction/csv_extractor.py) (add helper function)

**Implementation instructions:**

1. **Implement `_quarantine_error(file_path, error_type, error_message)`:**
   ```python
   def _quarantine_error(file_path: Path, error_type: str, error_message: str) -> None:
       quarantine_dir = Path("quarantine")
       quarantine_dir.mkdir(parents=True, exist_ok=True)
       error_file = quarantine_dir / "extraction_errors.csv"
       row = {
           "file_name": file_path.name,
           "file_path": str(file_path),
           "error_type": error_type,
           "error_message": error_message,
           "timestamp": datetime.utcnow().isoformat(),
       }
       write_header = not error_file.exists()
       with open(error_file, "a", newline="", encoding="utf-8") as f:
           writer = csv.DictWriter(f, fieldnames=row.keys())
           if write_header:
               writer.writeheader()
           writer.writerow(row)
   ```

2. **Call from `extract_csv_file`** inside the except block before re-raising.

3. **Optionally** copy the raw failed file to `quarantine/raw/{filename}` for post-mortem.

**Expected output:** A CSV at `quarantine/extraction_errors.csv` with one row per failure.

---

### Step 10 — Add Structured Logging Throughout

**Purpose:** Ensure every meaningful event during extraction is logged with structured context.

**Files to modify:** `extraction/csv_extractor.py`, `extraction/db_extractor.py`, `extraction/api_extractor.py`

**What to log:**

| Event | Level | Example Message |
|---|---|---|
| Scan cycle start | `INFO` | `Scanning data/incoming/ for new CSV files` |
| File detected | `INFO` | `Found file: 240101_Customer.csv` |
| File skipped (already processed) | `INFO` | `Skipping already-processed file: 240101_Customer.csv` |
| File skipped (unstable) | `WARNING` | `File is still being written: 240101_Customer.csv` |
| Filename pattern rejected | `WARNING` | `Unrecognized file pattern: report.csv` |
| Extraction success | `INFO` | `Extracted 600 rows from 240101_Customer.csv in 0.12s` |
| Schema mismatch | `ERROR` | `Missing columns in 240101_Customer.csv: {'pep', 'car'}` |
| Encoding error | `ERROR` | `UnicodeDecodeError reading 240101_Customer.csv, retrying with latin1` |
| Quarantine write | `WARNING` | `Quarantined 240101_Customer.csv — SchemaMismatch` |
| DB/API disabled | `INFO` | `DB extractor is disabled in configuration — skipping.` |

---

## 4. Suggested Project Files After Implementation

```
extraction/
├── __init__.py               # Re-exports public API
├── schema.py                 # Column constants + FILE_PATTERNS dict
├── csv_extractor.py          # ExtractionResult, extract_csv_file, scan_incoming, watch_directory
├── processed_tracker.py      # JSON-based file dedup (file_hash, is_processed, mark_processed)
├── db_extractor.py           # extract_db() stub
└── api_extractor.py          # extract_api() stub

config/
├── __init__.py               # (already exists)
├── config.yaml               # (already exists — no changes needed)
└── config_loader.py          # load_config() utility  [NEW]

tests/
├── __init__.py               # (already exists)
├── test_phase1_scaffold.py   # (already exists)
└── test_extraction.py        # Phase 2 extraction tests  [NEW]
```

---

## 5. Data Flow

```
data/incoming/240101_Customer.csv
        │
        ▼
  ┌─────────────┐
  │ scan_incoming│  ← polls data/incoming/ for *.csv
  └──────┬──────┘
         │ for each .csv file
         ▼
  ┌──────────────────┐
  │ _is_file_stable  │  ← size check with 1.5s delay
  └──────┬───────────┘
         │ stable?
         ▼
  ┌──────────────────┐
  │ classify_file    │  ← regex match against FILE_PATTERNS
  └──────┬───────────┘
         │ matched?
         ▼
  ┌──────────────────┐
  │ is_processed     │  ← check JSON tracker + SHA-256 hash
  └──────┬───────────┘
         │ new or changed?
         ▼
  ┌──────────────────┐
  │ pd.read_csv()    │  ← config-driven encoding, delimiter, quotechar
  └──────┬───────────┘
         │
         ▼
  ┌──────────────────┐
  │ schema validation│  ← compare df.columns vs expected columns
  └──────┬───────────┘
         │ valid?
         ▼
  ┌──────────────────┐
  │ mark_processed   │  ← persist hash to JSON tracker
  └──────┬───────────┘
         │
         ▼
  ExtractionResult(source, file_path, df, metadata)
         │
         ▼
  Transformation stage (Phase 3)
```

At each failure point, the flow branches to `_quarantine_error()` → `quarantine/extraction_errors.csv`.

---

## 6. Logging Strategy

- Initialize logging at pipeline startup via `logging_config.init_logging()` using the `level` and `file` from `config.yaml`.
- Every module creates its own logger: `logger = logging.getLogger(__name__)`.
- Log output goes to **both** `logs/pipeline.log` (file handler) and **stderr** (stream handler).
- Logged fields per extraction event: `filename`, `file_type`, `record_count`, `duration_seconds`, `file_hash`.
- Errors include the full exception traceback via `logger.exception()`.

---

## 7. Validation Checks

### 7.1 Filename Pattern Validation
- Match against `FILE_PATTERNS` regexes: `^\d{6}_Customer\.csv$` and `^\d{6}_Transactions\.csv$`.
- Reject non-matching files with a `WARNING` log — do not raise, just skip.

### 7.2 Schema Validation
- After reading the CSV, compare `df.columns.tolist()` against `CUSTOMER_COLUMNS` or `TRANSACTION_COLUMNS`.
- Compute `missing = set(expected) - set(actual)`.
- If `missing` is non-empty → `ValueError` + quarantine.

### 7.3 Encoding Validation
- Primary attempt uses `config.sources.csv.encoding` (default `utf-8`).
- On `UnicodeDecodeError`, retry with fallback stack: `utf-8-sig` → `latin1`.
- If all fail → quarantine with `EncodingError` type.

### 7.4 Delimiter Validation
- Use `config.sources.csv.delimiter` (default `,`).
- After reading, if only 1 column is returned (likely wrong delimiter), log a `WARNING` and quarantine.
- Heuristic: `len(df.columns) < 2` suggests delimiter mismatch.

---

## 8. Testing Procedure

### Test file: `tests/test_extraction.py`

| Test | What it Validates |
|---|---|
| `test_load_config` | `config_loader.load_config()` returns a dict with expected keys |
| `test_schema_constants` | `CUSTOMER_COLUMNS` has 12 items, `TRANSACTION_COLUMNS` has 7 items |
| `test_classify_file_valid` | `classify_file("240101_Customer.csv")` → `"customer"` |
| `test_classify_file_invalid` | `classify_file("report.csv")` → `None` |
| `test_extract_csv_customer` | Reads sample customer CSV → returns `ExtractionResult` with correct columns |
| `test_extract_csv_transactions` | Reads sample transactions CSV → returns `ExtractionResult` with correct columns |
| `test_processed_tracker_prevents_reprocessing` | After `mark_processed`, `is_processed` returns `True` |
| `test_processed_tracker_detects_change` | Modify file after marking → `is_processed` returns `False` |
| `test_extract_rejects_bad_schema` | CSV with missing columns → `ValueError` raised |
| `test_extract_quarantines_error` | Failed extraction → row appears in `quarantine/extraction_errors.csv` |
| `test_db_extractor_disabled` | `extract_db(config)` → `None` when `database.enabled` is `false` |
| `test_api_extractor_disabled` | `extract_api(config)` → `None` when `api.enabled` is `false` |

**Run command:**
```bash
pytest tests/test_extraction.py -v
```

**Setup requirements:**
- Copy sample CSVs with at least one data row to a temp directory for test fixtures.
- Use `tmp_path` pytest fixture for tracker JSON and quarantine files to avoid test pollution.

---

## 9. Common Implementation Pitfalls

| Pitfall | Impact | Mitigation |
|---|---|---|
| **Processing files mid-write** | Truncated DataFrames, parse errors | `_is_file_stable()` — compare file size before/after a delay |
| **Encoding mismatches** | `UnicodeDecodeError` crashes the scan loop | Fallback encoding stack + per-file exception handling |
| **Duplicate processing** | Same file extracted repeatedly on each scan cycle | SHA-256 hash tracker persisted to JSON |
| **Regex backslash issues** | Patterns fail on Windows paths | Use raw strings (`r"..."`) for all regex patterns |
| **Scan loop crashes on one bad file** | All remaining files in the batch are skipped | Wrap each file in a `try/except` inside the loop |
| **Tracker JSON corruption** | All dedup state lost | Atomic write (write to `.tmp` then rename) |
| **Relative path inconsistency** | Tracker records `./data/incoming/file.csv` vs `data/incoming/file.csv` | Always resolve to absolute path with `path.resolve()` |
| **Column name whitespace** | `" customer_id"` ≠ `"customer_id"` | Strip column names after read: `df.columns = df.columns.str.strip()` |

---

## 10. Definition of Done

All of the following conditions must be met:

- [ ] `extraction/` package contains `csv_extractor.py`, `schema.py`, `processed_tracker.py`, `db_extractor.py`, `api_extractor.py`
- [ ] `config/config_loader.py` loads `config.yaml` without errors
- [ ] Dropping a CSV matching `{YYMMDD}_Customer.csv` or `{YYMMDD}_Transactions.csv` into `data/incoming/` triggers extraction and returns an `ExtractionResult` with a valid DataFrame
- [ ] Running extraction a second time on the same file skips it (dedup via hash tracker)
- [ ] Modified files are detected and re-extracted (hash comparison)
- [ ] Files with invalid names are ignored with a logged warning
- [ ] Files with missing columns raise `ValueError` and are quarantined to `quarantine/extraction_errors.csv`
- [ ] Encoding errors trigger fallback retries; total failure is quarantined
- [ ] DB and API extractors return `None` when disabled, log an info message when enabled but unimplemented
- [ ] All tests in `tests/test_extraction.py` pass
- [ ] Extraction logs include file name, record count, and duration for every processed file
- [ ] The pipeline is ready to hand `ExtractionResult` objects to the Phase 3 transformation stage
