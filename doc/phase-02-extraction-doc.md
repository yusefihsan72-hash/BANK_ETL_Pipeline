# Phase 2: Extraction

## 1. Purpose
This phase implements the extraction layer for CSV, database, and API sources. The CSV source is the active ingestion path, while DB and API connectors are built as configuration-ready stubs.

## 2. Objectives
- Build a robust CSV extraction pipeline that reads files dropped into `data/incoming/`.
- Implement a directory watcher that detects new files and prevents reprocessing.
- Validate input files (filename, encoding, delimiter, schema) and log extraction metrics.
- Provide configuration-driven DB and API connector modules.

## 3. Scope
- Active extraction: CSV (`{YYMMDD}_Customer` and `{YYMMDD}_Transactions`).
- Passive connectors: DB and API extractors that read configuration and return placeholder DataFrames.
- Extraction output: `pandas.DataFrame` + metadata for downstream transformation.

## 4. Inputs Required
- `config/config.yaml` with extraction settings.
- Sample CSV files in `data/incoming/`:
  - `240101_Customer.csv`
  - `240101_Transactions.csv`
- Python environment with `pandas` installed.

## 5. Detailed Step-by-Step Implementation

### 5.1 Create Extraction Module Structure
1. Ensure the following files exist:
   - `extraction/__init__.py`
   - `extraction/csv_extractor.py`
   - `extraction/db_extractor.py`
   - `extraction/api_extractor.py`
   - `extraction/processed_tracker.py`
   - `extraction/schema.py`

### 5.2 Implement Configuration Loading (Prerequisite)
1. Create a config loader in `config/config_loader.py` (or reuse existing). Example:
```python
import yaml
from pathlib import Path

def load_config(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)
```
2. Ensure `config/config.yaml` contains:
```yaml
watcher:
  data_dir: "./data/incoming"
  processed_dir: "./data/processed"
  file_patterns:
    customer: "^\\d{6}_Customer\\.csv$"
    transaction: "^\\d{6}_Transactions\\.csv$"
  polling_interval_seconds: 10

sources:
  csv:
    enabled: true
    encoding: "utf-8"
    delimiter: ","
    quotechar: '"'

  database:
    enabled: false

  api:
    enabled: false
```

### 5.3 Define Expected Schemas (`extraction/schema.py`)
1. Create `extraction/schema.py` containing expected columns for each source:
```python
CUSTOMER_COLUMNS = [
    "customer_id", "age", "sex", "region", "income", "married",
    "children", "car", "save_act", "current_act", "mortgage", "pep",
]

TRANSACTION_COLUMNS = [
    "transaction_id", "customer_id", "date", "transaction_type", "amount",
    "balance", "description",
]

FILE_PATTERNS = {
    "customer": r"^\d{6}_Customer\.csv$",
    "transaction": r"^\d{6}_Transactions\.csv$",
}
```

### 5.4 Implement Processed-File Tracking (`extraction/processed_tracker.py`)
1. Choose a tracking store. Two recommended options:
   - **JSON-based**: `data/processed/processed_files.json`
   - **SQLite-based**: `data/processed/processed_files.db` with table `processed_files`

2. Implement a simple interface:
```python
from pathlib import Path
import json
import hashlib

TRACKER_PATH = Path("data/processed/processed_files.json")

def _load_tracker():
    if TRACKER_PATH.exists():
        return json.loads(TRACKER_PATH.read_text())
    return {}

def _save_tracker(data):
    TRACKER_PATH.parent.mkdir(parents=True, exist_ok=True)
    TRACKER_PATH.write_text(json.dumps(data, indent=2))

def file_hash(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hasher.update(chunk)
    return hasher.hexdigest()

def is_processed(path: Path) -> bool:
    tracker = _load_tracker()
    return tracker.get(str(path.resolve())) is not None

def mark_processed(path: Path, file_hash: str):
    tracker = _load_tracker()
    tracker[str(path.resolve())] = {
        "hash": file_hash,
        "processed_at": datetime.utcnow().isoformat(),
    }
    _save_tracker(tracker)
```

3. Optionally, implement SQLite version for atomic writes and concurrency.

### 5.5 Implement File Watcher Logic (`extraction/csv_extractor.py`)

#### 5.5.1 Core Extraction Function
1. Define an extraction result dataclass:
```python
from dataclasses import dataclass
from pathlib import Path
import pandas as pd

@dataclass
class ExtractionResult:
    source: str
    file_path: Path
    df: pd.DataFrame
    metadata: dict
```

2. Implement `extract_csv_file()`:
```python
import time
import pandas as pd
import logging
from extraction.schema import CUSTOMER_COLUMNS, TRANSACTION_COLUMNS, FILE_PATTERNS
from extraction.processed_tracker import is_processed, mark_processed, file_hash

logger = logging.getLogger(__name__)

def extract_csv_file(file_path: Path, config: dict) -> ExtractionResult:
    start = time.perf_counter()
    filetype = "customer" if "Customer" in file_path.name else "transaction"

    # Pattern validation
    pattern = FILE_PATTERNS[filetype]
    if not re.match(pattern, file_path.name):
        raise ValueError(f"Unexpected filename: {file_path.name}")

    if is_processed(file_path):
        logger.info("Skipping already processed file: %s", file_path)
        return None

    encoding = config["sources"]["csv"]["encoding"]
    delimiter = config["sources"]["csv"]["delimiter"]

    try:
        df = pd.read_csv(
            file_path,
            encoding=encoding,
            delimiter=delimiter,
            quotechar=config["sources"]["csv"].get("quotechar", '"'),
        )
    except UnicodeDecodeError as e:
        # Try fallback encodings
        for enc in ["utf-8-sig", "latin1"]:
            try:
                df = pd.read_csv(file_path, encoding=enc, delimiter=delimiter)
                break
            except Exception:
                df = None
        if df is None:
            raise

    expected_cols = CUSTOMER_COLUMNS if filetype == "customer" else TRANSACTION_COLUMNS
    missing = set(expected_cols) - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    file_hash_val = file_hash(file_path)
    mark_processed(file_path, file_hash_val)

    metadata = {
        "file_name": file_path.name,
        "file_path": str(file_path),
        "record_count": len(df),
        "start_time": start,
        "end_time": time.perf_counter(),
        "duration_seconds": time.perf_counter() - start,
        "file_hash": file_hash_val,
    }

    return ExtractionResult(source=filetype, file_path=file_path, df=df, metadata=metadata)
```

#### 5.5.2 Watcher Loop
1. Implement `watch_directory(config)`:
```python
import time
from pathlib import Path


def watch_directory(config):
    data_dir = Path(config["watcher"]["data_dir"])
    polling = config["watcher"].get("polling_interval_seconds", 10)

    while True:
        for file_path in data_dir.glob("*.csv"):
            try:
                result = extract_csv_file(file_path, config)
                if result:
                    # Send to transformation pipeline
                    pass
            except Exception as e:
                logger.exception("Failed to extract %s: %s", file_path, e)
        time.sleep(polling)
```

2. Add a file-stability check to avoid processing files mid-write:
   - Capture file size, wait 1–2 seconds, re-check size; only process if stable.
   - Alternatively, require files be written with a temporary suffix (e.g., `.tmp`) and renamed.

### 5.6 Logging Extraction Metrics
1. Ensure `logging_config.py` is used to initialize logging.
2. In `extract_csv_file()`, log:
   - Start and end extraction
   - File name, record count, duration
   - Any schema or read errors
3. Example log calls:
```python
logger.info("Extracted %s rows from %s in %.2fs", len(df), file_path.name, metadata["duration_seconds"])
```

### 5.7 Create DB and API Connector Stubs

#### 5.7.1 `extraction/db_extractor.py`
1. Implement a function `extract_db(config: dict) -> ExtractionResult`.
2. Log that the connector is configured but not active.
3. Return an empty DataFrame or mock sample for now.

Example stub:
```python
import pandas as pd
import logging

logger = logging.getLogger(__name__)

def extract_db(config: dict):
    if not config["sources"]["database"]["enabled"]:
        return None

    logger.info("DB extractor configured but not enabled for active extraction")
    return pd.DataFrame()
```

#### 5.7.2 `extraction/api_extractor.py`
1. Implement a function `extract_api(config: dict) -> ExtractionResult`.
2. Handle base URL and auth values from config.
3. Add stubbed pagination logic (e.g., loop a fixed number of pages and return empty DF).

### 5.8 Error Handling and Quarantine
1. Create `quarantine/` directory to store failure records.
2. When extraction fails (e.g., parsing error, schema mismatch), write metadata to `quarantine/extraction_errors.csv` with columns:
   - `file_name`, `error_type`, `error_message`, `timestamp`.
3. Optionally, copy the raw file to `quarantine/raw/` for inspection.

### 5.9 Hand Off to Transformation
1. Define a pipeline interface that accepts `ExtractionResult` objects.
2. For now, write a simple in-memory queue or function call where extraction yields results to the next stage.

## 6. Suggested File/Module Responsibilities

| File | Responsibility |
|---|---|
| `extraction/csv_extractor.py` | Watch directory, validate files, read CSV into DataFrame, compute metadata | 
| `extraction/processed_tracker.py` | Track processed files to prevent reprocessing | 
| `extraction/schema.py` | Define expected column sets and filename patterns | 
| `extraction/db_extractor.py` | Stubbed DB connector, config-driven | 
| `extraction/api_extractor.py` | Stubbed API connector, config-driven | 
| `config/config_loader.py` | Load YAML configuration | 
| `logging_config.py` | Configure logging for extraction and pipeline | 

## 7. Outputs / Deliverables
- `extraction/` module with working CSV extraction logic.
- Processed-file tracker preventing reprocessing.
- Logging output containing extraction metrics.
- Quarantine artifacts for malformed files.
- DB and API extractor stubs ready for future expansion.

## 8. Dependencies
- Python 3.10+
- pandas
- pyyaml
- Optional: watchdog (for file watch) or built-in polling logic.

## 9. Risks and Mitigations
- **Risk:** Files are processed while still being written.  
  **Mitigation:** Use file-size stability checks and/or require a `.ready` rename before processing.

- **Risk:** Files change after being marked processed.  
  **Mitigation:** Use file hashing to detect changes and reprocess if hash differs.

- **Risk:** Schema changes cause extraction to break.  
  **Mitigation:** Log and quarantine schema-mismatched files, and document required schema.

## 10. Validation Checklist
- [ ] New CSV file dropped into `data/incoming/` is detected and processed.
- [ ] Processed files are marked to prevent reprocessing.
- [ ] Extraction logs include record count, duration, and file metadata.
- [ ] Invalid files (bad schema, encoding errors) are recorded in quarantine.
- [ ] DB and API connectors load configuration and return placeholder DataFrames.

## 11. Acceptance Criteria
- CSV extraction pipeline reads `Customer` and `Transactions` files and outputs DataFrames with expected columns.
- Each file is processed only once, even if the pipeline is rerun.
- Errors during extraction are logged and quarantined with failure reasons.
- Extraction metrics (record counts, runtime, metadata) are captured in logs.

## 12. Definition of Done
- `extraction/` contains functional CSV extraction code and supporting modules.
- Processed-file tracking prevents reprocessing and persists across runs.
- The pipeline can be started and will process sample files without errors.
- The output DataFrames are ready for the transformation layer (correct column structure).
- The project includes documentation explaining how to run the extraction stage.
