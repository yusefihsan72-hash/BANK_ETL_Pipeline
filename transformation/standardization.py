# transformation/standardization.py

import pandas as pd

SEX_MAP = {"M": "M", "F": "F", "MALE": "M", "FEMALE": "F"}


def standardize_customers(df: pd.DataFrame) -> pd.DataFrame:
    """
    Standardize the customer DataFrame.
    Renames '_id' → 'customer_id' to match the rest of the pipeline.
    """
    df = df.copy()

    # Rename '_id' to 'customer_id'
    if "_id" in df.columns:
        df.rename(columns={"_id": "customer_id"}, inplace=True)

    # Normalize sex column
    df["sex"] = df["sex"].astype(str).str.strip().str.upper().map(SEX_MAP)

    # Normalize region
    df["region"] = df["region"].astype(str).str.strip().str.upper() \
                               .str.replace(" ", "_").str.replace("-", "_")

    # Convert numeric fields — strip commas first
    for col in ["income", "save_act", "current_act"]:
        if col in df.columns:
            df[col] = pd.to_numeric(
                df[col].astype(str).str.replace(",", ""), errors="coerce")

    # Convert boolean-like fields
    bool_map = {"YES": True, "NO": False, "1": True, "0": False}
    for col in ["married", "car", "mortgage", "pep"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip().str.upper().map(bool_map)

    # Convert age to numeric
    df["age"] = pd.to_numeric(df["age"], errors="coerce")

    return df


def standardize_transactions(df: pd.DataFrame) -> pd.DataFrame:
    """
    Standardize the transaction DataFrame.
    Renames real CSV columns to the pipeline's expected schema.

    Real columns:  customer_id | Date | Description | Deposits | Withdrawls | Balance
    Output schema: customer_id | date | description | deposits | withdrawals | balance
                   + amount (combined: deposits - withdrawals)
                   + transaction_id (generated from row index)
    """
    df = df.copy()

    # Normalize column names to lowercase
    df.columns = [c.strip() for c in df.columns]
    df.rename(columns={
        "Date":        "date",
        "Description": "description",
        "Deposits":    "deposits",
        "Withdrawls":  "withdrawals",   # fix typo in source
        "Balance":     "balance",
    }, inplace=True)

    # Parse date
    df["date"] = pd.to_datetime(df["date"], errors="coerce", dayfirst=True)

    # Clean numeric fields — remove commas and convert
    for col in ["deposits", "withdrawals", "balance"]:
        if col in df.columns:
            df[col] = pd.to_numeric(
                df[col].astype(str).str.replace(",", ""), errors="coerce"
            ).fillna(0.0)

    # Derive a single 'amount' column:
    # deposits are positive, withdrawals are negative
    df["amount"] = df["deposits"] - df["withdrawals"]

    # Derive 'transaction_type' from description
    df["transaction_type"] = df["description"].astype(str).str.strip().str.title()

    # Generate a unique transaction_id since the source has none
    df["transaction_id"] = (
        df["customer_id"].astype(str) + "_" +
        df["date"].dt.strftime("%Y%m%d") + "_" +
        df.groupby(["customer_id", "date"]).cumcount().add(1).astype(str)
    )

    return df