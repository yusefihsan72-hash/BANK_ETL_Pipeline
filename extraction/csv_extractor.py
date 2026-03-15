# extraction/csv_extractor.py
import re, time, logging
from dataclasses import dataclass
from pathlib import Path
import pandas as pd
from extraction.schema import CUSTOMER_COLUMNS, TRANSACTION_COLUMNS, FILE_PATTERNS
from extraction.processed_tracker import is_processed, mark_processed, file_hash

logger = logging.getLogger(__name__)

@dataclass
class ExtractionResult:
    source: str
    file_path: Path
    df: pd.DataFrame
    metadata: dict

def extract_csv_file(file_path: Path, config: dict):
    start = time.perf_counter()
    filetype = "customer" if "Customer" in file_path.name else "transaction"

    if not re.match(FILE_PATTERNS[filetype], file_path.name):
        raise ValueError(f"Invalid filename: {file_path.name}")
    if is_processed(file_path):
        logger.info("Skipping (already processed): %s", file_path.name)
        return None

    csv_cfg = config["sources"]["csv"]
    df = pd.read_csv(file_path, encoding=csv_cfg["encoding"],
                     delimiter=csv_cfg["delimiter"])
    
    expected = CUSTOMER_COLUMNS if filetype == "customer" else TRANSACTION_COLUMNS
    missing = set(expected) - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns: {missing}")

    h = file_hash(file_path)
    mark_processed(file_path, h)
    duration = time.perf_counter() - start
    logger.info("Extracted %d rows from %s in %.2fs", len(df), file_path.name, duration)

    return ExtractionResult(
        source=filetype, file_path=file_path, df=df,
        metadata={"file_name": file_path.name, "record_count": len(df),
                  "duration_seconds": duration, "file_hash": h}
    )

def watch_directory(config):
    from pathlib import Path
    import time
    data_dir = Path(config["watcher"]["data_dir"])
    polling = config["watcher"].get("polling_interval_seconds", 10)
    while True:
        for fp in data_dir.glob("*.csv"):
            try:
                result = extract_csv_file(fp, config)
                if result:
                    yield result
            except Exception as e:
                logger.exception("Failed: %s - %s", fp.name, e)
        time.sleep(polling)