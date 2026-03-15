# pipeline/run.py

import time
import logging
import csv
from datetime import datetime
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
# File Processing
# ─────────────────────────────────────────────────────────────

def process_file(file_path: Path, config: dict, loader: WarehouseLoader) -> None:
    """
    Process a single CSV file through the full ETL pipeline:
    Extract → Transform → Validate → Load.

    Skips files that are still being written (unstable size).
    Skips files that have already been processed (tracked by hash).
    Sends pipeline-level failures to the quarantine error log.

    Args:
        file_path: Path to the CSV file to process.
        config:    Full pipeline configuration dictionary.
        loader:    Active WarehouseLoader instance for DB operations.
    """
    # -- File stability check -------------------------------------
    # Wait 1 second and compare file size before and after.
    # If the size changed, the file is still being written — skip it.
    size_before = file_path.stat().st_size
    time.sleep(1)
    size_after = file_path.stat().st_size

    if size_before != size_after:
        logger.info("File is still being written, skipping: %s", file_path.name)
        return

    # -- Extraction -----------------------------------------------
    # extract_csv_file returns None if the file was already processed.
    result = extract_csv_file(file_path, config)
    if result is None:
        return

    logger.info("[EXTRACT] %s → %d rows extracted", file_path.name, len(result.df))

    # -- Route to the correct processing function -----------------
    try:
        if result.source == "customer":
            _process_customers(result.df, loader)

        elif result.source == "transaction":
            _process_transactions(result.df, loader)

        else:
            logger.warning("Unknown source type '%s' for file: %s",
                           result.source, file_path.name)

    except Exception as e:
        # Log the full traceback and write the file to the error quarantine.
        logger.exception("Pipeline failed for file %s: %s", file_path.name, e)
        _quarantine_file(file_path, str(e))


# ─────────────────────────────────────────────────────────────
# Customer Processing
# ─────────────────────────────────────────────────────────────

def _process_customers(df, loader: WarehouseLoader) -> None:
    """
    Run the Transform → Validate → Load pipeline for customer data.

    Steps:
        1. Standardize categorical values and data types.
        2. Clean: drop missing keys, flag nulls, remove duplicates.
        3. Validate: schema, completeness, uniqueness, range checks.
        4. Save failed records to quarantine CSV.
        5. Save validation summary report.
        6. Load valid records into dim_customer.

    Args:
        df:     Extracted customer DataFrame.
        loader: Active WarehouseLoader instance.
    """
    # Step 1 & 2 — Transform
    df = standardize_customers(df)
    df = clean_customers(df)
    logger.info("[TRANSFORM] customers → %d rows after cleaning", len(df))

    # Step 3 — Validate
    passed, failed = validate_customers(df)
    logger.info("[VALIDATE] customers → %d passed / %d failed",
                len(passed), len(failed))

    # Step 4 & 5 — Quarantine + Report
    save_quarantine(failed, "customer")
    save_summary(len(passed), len(failed), "customer")

    # Step 6 — Load
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
    Run the Transform → Validate → Load pipeline for transaction data.

    Steps:
        1. Standardize dates, amounts, and transaction types.
        2. Clean: drop missing keys, flag nulls, remove duplicates.
        3. Enrich: derive date parts, amount flags (is_debit, is_credit).
        4. Validate: schema, completeness, uniqueness, allowed values.
        5. Save failed records to quarantine CSV.
        6. Save validation summary report.
        7. Load valid records into dimension tables, then fact table.
           Load order: dim_date → dim_transaction_type →
                       dim_account_profile → fact_transactions.

    Args:
        df:     Extracted transaction DataFrame.
        loader: Active WarehouseLoader instance.
    """
    # Step 1, 2 & 3 — Transform + Enrich
    df = standardize_transactions(df)
    df = clean_transactions(df)
    df = enrich_transactions(df)
    logger.info("[TRANSFORM] transactions → %d rows after cleaning", len(df))

    # Step 4 — Validate
    passed, failed = validate_transactions(df)
    logger.info("[VALIDATE] transactions → %d passed / %d failed",
                len(passed), len(failed))

    # Step 5 & 6 — Quarantine + Report
    save_quarantine(failed, "transactions")
    save_summary(len(passed), len(failed), "transactions")

    # Step 7 — Load dimensions first, then fact table
    # Dimension tables must be loaded before the fact table
    # to ensure all foreign keys exist before inserting facts.
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
# Error Quarantine
# ─────────────────────────────────────────────────────────────

def _quarantine_file(file_path: Path, error_msg: str) -> None:
    """
    Record a pipeline-level file failure in the error quarantine log.

    Appends one row per failure to quarantine/pipeline_errors.csv.
    Creates the file and header automatically on first write.

    Columns: file_name | error_message | timestamp

    Args:
        file_path:  Path to the file that caused the failure.
        error_msg:  String representation of the exception.
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
            datetime.utcnow().isoformat()
        ])

    logger.info("File failure recorded in quarantine: %s", file_path.name)


# ─────────────────────────────────────────────────────────────
# Directory Watcher — Infinite Loop
# ─────────────────────────────────────────────────────────────

def watch_directory(config: dict, loader: WarehouseLoader) -> None:
    """
    Continuously poll the incoming data directory for new CSV files.

    Runs an infinite loop with a configurable sleep interval.
    On each iteration:
        - Scans data_dir for all *.csv files.
        - Filters out already-processed files using the tracker.
        - Processes each new file in sorted (deterministic) order.
        - Logs a debug message if no new files are found.

    The loop only stops when a KeyboardInterrupt (Ctrl+C) is received,
    which is re-raised to be handled cleanly by run_pipeline().

    Args:
        config: Full pipeline configuration dictionary.
        loader: Active WarehouseLoader instance shared across iterations.
    """
    data_dir = Path(config["watcher"]["data_dir"])
    polling  = config["watcher"].get("polling_interval_seconds", 10)

    logger.info("=" * 55)
    logger.info("Pipeline watching directory: %s", data_dir)
    logger.info("Poll interval: %ds | Press Ctrl+C to stop", polling)
    logger.info("=" * 55)

    while True:
        try:
            # Collect all CSV files in the incoming directory
            csv_files = list(data_dir.glob("*.csv"))

            if csv_files:
                # Filter to only files not yet processed
                new_files = [f for f in csv_files if not is_processed(f)]

                if new_files:
                    logger.info("Found %d new file(s) to process", len(new_files))
                    # Sort ensures deterministic processing order
                    for file_path in sorted(new_files):
                        logger.info("-- Processing: %s", file_path.name)
                        process_file(file_path, config, loader)
                else:
                    logger.debug("No new files found. Waiting...")
            else:
                logger.debug("Directory is empty. Waiting...")

        except KeyboardInterrupt:
            # Re-raise so run_pipeline() can handle shutdown cleanly
            raise

        except Exception as e:
            # Log unexpected errors in the watch loop but keep running
            logger.exception("Unexpected error in watch loop: %s", e)

        # Wait before the next scan
        time.sleep(polling)


# ─────────────────────────────────────────────────────────────
# Pipeline Entry Point
# ─────────────────────────────────────────────────────────────

def run_pipeline(config: dict = None) -> None:
    """
    Main entry point for the ETL pipeline.

    Responsibilities:
        1. Load configuration from config/config.yaml (or use provided config).
        2. Initialize logging (file + console handlers).
        3. Create the WarehouseLoader (connects to SQLite, creates tables).
        4. Start the infinite directory watcher loop.
        5. Handle graceful shutdown on Ctrl+C.
        6. Ensure the database connection is closed on exit.

    Args:
        config: Optional pre-loaded config dictionary.
                If None, loads from 'config/config.yaml'.
                Primarily used to inject test configs in unit tests.
    """
    # Step 1 — Load config
    if config is None:
        config = load_config("config/config.yaml")

    # Step 2 — Initialize logging
    init_logging(
        log_file=config["logging"]["file"],
        level=config["logging"].get("level", "INFO")
    )

    logger.info("Pipeline starting up...")

    # Step 3 — Initialize warehouse loader
    # This creates the SQLite database and all tables if they don't exist.
    loader = WarehouseLoader()

    # Step 4 — Start watching for new files
    try:
        watch_directory(config, loader)

    except KeyboardInterrupt:
        # Step 5 — Graceful shutdown on Ctrl+C
        logger.info("Pipeline stopped by user (Ctrl+C). Shutting down...")

    finally:
        # Step 6 — Always close the DB connection on exit
        if hasattr(loader, "conn") and loader.conn:
            loader.conn.close()
            logger.info("Database connection closed.")

    logger.info("Pipeline shutdown complete.")


# ─────────────────────────────────────────────────────────────
# Script Entry Point
# ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    run_pipeline()