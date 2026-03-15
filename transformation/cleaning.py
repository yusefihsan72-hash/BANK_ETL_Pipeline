# transformation/cleaning.py
import pandas as pd
import logging

logger = logging.getLogger(__name__)

def drop_missing_keys(df: pd.DataFrame, key_columns: list) -> pd.DataFrame:
    before = len(df)
    df = df.dropna(subset=key_columns)
    dropped = before - len(df)
    if dropped:
        logger.warning("Dropped %d rows with missing keys: %s", dropped, key_columns)
    return df

def flag_missing(df: pd.DataFrame, columns: list, suffix="_missing") -> pd.DataFrame:
    df = df.copy()
    for col in columns:
        df[f"{col}{suffix}"] = df[col].isna()
    return df

def deduplicate(df: pd.DataFrame, subset: list, keep="first") -> pd.DataFrame:
    before = len(df)
    df = df.drop_duplicates(subset=subset, keep=keep)
    dups = before - len(df)
    if dups:
        logger.warning("Removed %d duplicates on %s", dups, subset)
    return df

def clean_customers(df: pd.DataFrame) -> pd.DataFrame:
    df = drop_missing_keys(df, ["customer_id"])
    df = flag_missing(df, ["income", "age"])
    df = deduplicate(df, ["customer_id"])
    # تحقق من نطاق العمر
    mask = df["age"].notna() & ((df["age"] < 18) | (df["age"] > 120))
    df.loc[mask, ["age", "age_missing"]] = [None, True]
    return df

def clean_transactions(df: pd.DataFrame) -> pd.DataFrame:
    df = drop_missing_keys(df, ["transaction_id", "date", "amount"])
    df = flag_missing(df, ["balance", "description"])
    df = deduplicate(df, ["transaction_id"])
    return df