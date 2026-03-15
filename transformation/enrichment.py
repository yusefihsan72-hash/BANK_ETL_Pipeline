# transformation/enrichment.py
import pandas as pd

def derive_date_parts(df: pd.DataFrame, date_col="date") -> pd.DataFrame:
    df = df.copy()
    dt = pd.to_datetime(df[date_col], errors="coerce")
    df["transaction_year"] = dt.dt.year
    df["transaction_month"] = dt.dt.month
    df["transaction_day_of_week"] = dt.dt.dayofweek
    df["transaction_quarter"] = dt.dt.quarter
    return df

def derive_amount_flags(df: pd.DataFrame, amount_col="amount") -> pd.DataFrame:
    df = df.copy()
    df["amount_abs"] = df[amount_col].abs()
    df["is_debit"] = df[amount_col] < 0
    df["is_credit"] = df[amount_col] >= 0
    return df

def enrich_transactions(df: pd.DataFrame) -> pd.DataFrame:
    df = derive_date_parts(df)
    df = derive_amount_flags(df)
    return df