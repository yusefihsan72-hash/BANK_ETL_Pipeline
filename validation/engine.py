# validation/engine.py
import pandas as pd
import logging
from validation.rules import (validate_completeness, validate_uniqueness,
                               validate_range, validate_allowed_values)

logger = logging.getLogger(__name__)

TRANSACTION_TYPES = ["ATM", "Transfer", "Bill", "Interest", "Deposit", "Withdrawal"]

def validate_customers(df: pd.DataFrame):
    failures = {}
    all_f = (
        validate_completeness(df, ["customer_id", "age", "sex", "region"]) +
        validate_uniqueness(df, ["customer_id"]) +
        validate_range(df, "age", 18, 120)
    )
    for f in all_f:
        failures.setdefault(f.row_index, []).append(f.failure_reason)
    return _split(df, failures)

def validate_transactions(df: pd.DataFrame):
    failures = {}
    all_f = (
        validate_completeness(df, ["transaction_id", "customer_id", "date", "amount"]) +
        validate_uniqueness(df, ["transaction_id"]) +
        validate_allowed_values(df, "transaction_type", TRANSACTION_TYPES)
    )
    for f in all_f:
        failures.setdefault(f.row_index, []).append(f.failure_reason)
    return _split(df, failures)

def _split(df: pd.DataFrame, failures: dict):
    failed_idx = set(failures.keys())
    passed_df = df[~df.index.isin(failed_idx)].copy()
    failed_df = df[df.index.isin(failed_idx)].copy()
    failed_df["failure_reasons"] = failed_df.index.map(
        lambda i: "; ".join(failures[i]))
    logger.info("Validation: %d passed / %d failed", len(passed_df), len(failed_df))
    return passed_df, failed_df