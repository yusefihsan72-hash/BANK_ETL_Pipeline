# pipeline/run.py

import time
import logging
import csv
import shutil
from datetime import datetime, timezone
from pathlib import Path

from config.config_loader import load_config
from config.logging_config import init_logging
from extraction.csv_extractor import extract_csv_file
from extraction.processed_tracker import is_processed
from transformation.standardization import standardize_customers, standardize_transactions
from transformation.cleaning import clean_customers, clean_transactions
from transformation.enrichment import enrich_transactions
from validation.engine import validate_customers, validate_transactions
from validation.report import save_quarantine, save_summary
from warehouse.loader import WarehouseLoader

logger = logging.getLogger("pipeline")


# ─────────────────────────────────────────────────────────────
# Archive Helper
# ─────────────────────────────────────────────────────────────

def archive_file(file_path: Path, config: dict) -> Path:
    """
    Move a successfully processed CSV file to the archive folder.

    Archive structure:
        data/archive/YYYY/MM/DD/<original_filename>

    If a file with the same name already exists in the archive,
    a timestamp suffix is added to avoid overwriting it:
        240101_Customer_20240110_153045.csv

    Args:
        file_path: Path to the processed CSV file.
        config:    Full pipeline configuration dictionary.

    Returns:
        The final archive path where the file was moved.
    """
    # Read archive root from config — default to data/archive
    archive_root = Path(
        config.get("watcher", {}).get("archive_dir", "data/archive")
    )

    # Organize into sub-folders by date: YYYY/MM/DD
    today        = datetime.now(timezone.utc)
    archive_dir  = archive_root / str(today.year) \
                                / f"{today.month:02d}" \
                                / f"{today.day:02d}"
    archive_dir.mkdir(parents=True, exist_ok=True)

    destination = archive_dir / file_path.name

    # If file already exists in archive — add timestamp suffix
    if destination.exists():
        stem      = file_path.stem
        suffix    = file_path.suffix
        timestamp = today.strftime("%Y%m%d_%H%M%S")
        destination = archive_dir / f"{stem}_{timestamp}{suffix}"

    shutil.move(str(file_path), str(destination))
    logger.info("[ARCHIVE] %s → %s", file_path.name, destination)

    return destination


# ─────────────────────────────────────────────────────────────
# Error Quarantine
# ─────────────────────────────────────────────────────────────

def _quarantine_file(file_path: Path, error_msg: str) -> None:
    """
    Record a pipeline-level file failure in the error quarantine log.
    Appends one row per failure to quarantine/pipeline_errors.csv.

    Columns: file_name | error_message | timestamp
    """
    q_path = Path("quarantine") / "pipeline_errors.csv"
    q_path.parent.mkdir(parents=True, exist_ok=True)

    write_header = not q_path.exists()

    with q_path.open("a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if write_header:
            writer.writerow(["file_name", "error_message", "timestamp"])
        writer.writerow([
            file_path.name,
            error_msg,
            datetime.now(timezone.utc).isoformat(),
        ])

    logger.info("[QUARANTINE] Failure recorded for: %s", file_path.name)


# ─────────────────────────────────────────────────────────────
# Customer Processing
# ─────────────────────────────────────────────────────────────

def _process_customers(df, loader: WarehouseLoader) -> None:
    """
    Transform → Validate → Load pipeline for customer data.
    """
    # Transform
    df = standardize_customers(df)
    df = clean_customers(df)
    logger.info("[TRANSFORM] customers → %d rows after cleaning", len(df))

    # Validate
    passed, failed = validate_customers(df)
    logger.info("[VALIDATE] customers → %d passed / %d failed",
                len(passed), len(failed))

    # Quarantine + Report
    save_quarantine(failed, "customer")
    save_summary(len(passed), len(failed), "customer")

    # Load
    if not passed.empty:
        loader.load_dim_customer(passed)
        logger.info("[LOAD] dim_customer → %d rows loaded", len(passed))
    else:
        logger.warning("[LOAD] No valid customer rows to load.")


# ─────────────────────────────────────────────────────────────
# Transaction Processing
# ─────────────────────────────────────────────────────────────

def _process_transactions(df, loader: WarehouseLoader) -> None:
    """
    Transform → Validate → Load pipeline for transaction data.
    Loads dimension tables first, then the fact table.
    """
    # Transform
    df = standardize_transactions(df)
    df = clean_transactions(df)
    df = enrich_transactions(df)
    logger.info("[TRANSFORM] transactions → %d rows after cleaning", len(df))

    # Validate
    passed, failed = validate_transactions(df)
    logger.info("[VALIDATE] transactions → %d passed / %d failed",
                len(passed), len(failed))

    # Quarantine + Report
    save_quarantine(failed, "transactions")
    save_summary(len(passed), len(failed), "transactions")

    # Load dimensions first, then fact
    if not passed.empty:
        loader.load_dim_date(passed)
        logger.info("[LOAD] dim_date loaded")

        loader.load_dim_transaction_type(passed)
        logger.info("[LOAD] dim_transaction_type loaded")

        loader.load_dim_account_profile(passed)
        logger.info("[LOAD] dim_account_profile loaded")

        loader.load_fact_transactions(passed)
        logger.info("[LOAD] fact_transactions → %d rows loaded", len(passed))
    else:
        logger.warning("[LOAD] No valid transaction rows to load.")


# ─────────────────────────────────────────────────────────────
# File Processing
# ─────────────────────────────────────────────────────────────

def process_file(file_path: Path, config: dict, loader: WarehouseLoader) -> None:
    """
    Process a single CSV file through the full ETL pipeline:
        Extract → Transform → Validate → Load → Archive

    On success: file is moved to data/archive/YYYY/MM/DD/
    On failure: error is logged in quarantine/pipeline_errors.csv
                and the file stays in data/incoming/ for inspection.

    Args:
        file_path: Path to the CSV file to process.
        config:    Full pipeline configuration dictionary.
        loader:    Active WarehouseLoader instance.
    """
    # -- File stability check ---------------------------------
    # If the file size changes within 1 second it is still
    # being written — skip it and retry on the next poll cycle.
    size_before = file_path.stat().st_size
    time.sleep(1)
    size_after  = file_path.stat().st_size

    if size_before != size_after:
        logger.info("[SKIP] File still being written: %s", file_path.name)
        return

    # -- Extraction -------------------------------------------
    result = extract_csv_file(file_path, config)
    if result is None:
        # Already processed in a previous run — archive it now
        # in case it was left behind after a crash
        archive_file(file_path, config)
        return

    logger.info("[EXTRACT] %s → %d rows", file_path.name, len(result.df))

    # -- Route to correct processing function -----------------
    try:
        if result.source == "customer":
            _process_customers(result.df, loader)

        elif result.source == "transaction":
            _process_transactions(result.df, loader)

        else:
            logger.warning("[SKIP] Unknown source type '%s': %s",
                           result.source, file_path.name)
            return

        # -- Archive on success -------------------------------
        archive_path = archive_file(file_path, config)
        logger.info("[DONE] %s successfully processed and archived → %s",
                    file_path.name, archive_path)

    except Exception as e:
        # Log full traceback, record in quarantine error log.
        # File stays in data/incoming/ for manual inspection.
        logger.exception("[ERROR] Pipeline failed for %s: %s",
                         file_path.name, e)
        _quarantine_file(file_path, str(e))


# ─────────────────────────────────────────────────────────────
# Directory Watcher — Infinite Loop
# ─────────────────────────────────────────────────────────────

def watch_directory(config: dict, loader: WarehouseLoader) -> None:
    """
    Continuously poll the incoming directory for new CSV files.

    Each iteration:
        1. Scan data/incoming/ for *.csv files.
        2. Filter out already-processed files.
        3. Process each new file → archive on success.
        4. Sleep for polling_interval_seconds.

    Stops only on KeyboardInterrupt (Ctrl+C).
    """
    data_dir = Path(config["watcher"]["data_dir"])
    polling  = config["watcher"].get("polling_interval_seconds", 10)

    # Ensure archive root exists at startup
    archive_root = Path(config.get("watcher", {}).get("archive_dir", "data/archive"))
    archive_root.mkdir(parents=True, exist_ok=True)

    logger.info("=" * 55)
    logger.info("Pipeline watching : %s", data_dir)
    logger.info("Archive folder    : %s", archive_root)
    logger.info("Poll interval     : %ds | Ctrl+C to stop", polling)
    logger.info("=" * 55)

    while True:
        try:
            csv_files = list(data_dir.glob("*.csv"))

            if csv_files:
                new_files = [f for f in csv_files if not is_processed(f)]
                if new_files:
                    logger.info("Found %d new file(s) to process", len(new_files))
                    for file_path in sorted(new_files):
                        logger.info("── Processing: %s", file_path.name)
                        process_file(file_path, config, loader)
                else:
                    logger.debug("No new files — waiting...")
            else:
                logger.debug("Directory empty — waiting...")

        except KeyboardInterrupt:
            raise

        except Exception as e:
            logger.exception("Unexpected error in watch loop: %s", e)

        time.sleep(polling)


# ─────────────────────────────────────────────────────────────
# Pipeline Entry Point
# ─────────────────────────────────────────────────────────────

def run_pipeline(config: dict = None) -> None:
    """
    Main entry point for the ETL pipeline.

    1. Load config from config/config.yaml.
    2. Initialize logging.
    3. Create WarehouseLoader (connects to SQLite, creates tables).
    4. Start infinite directory watcher loop.
    5. Graceful shutdown on Ctrl+C.
    6. Close DB connection on exit.
    """
    if config is None:
        config = load_config("config/config.yaml")

    init_logging(
        log_file=config["logging"]["file"],
        level=config["logging"].get("level", "INFO"),
    )

    logger.info("Pipeline starting...")

    loader = WarehouseLoader()

    try:
        watch_directory(config, loader)

    except KeyboardInterrupt:
        logger.info("Pipeline stopped by user (Ctrl+C).")

    finally:
        if hasattr(loader, "conn") and loader.conn:
            loader.conn.close()
            logger.info("Database connection closed.")

    logger.info("Pipeline shutdown complete.")


# ─────────────────────────────────────────────────────────────
# Script Entry Point
# ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    run_pipeline()