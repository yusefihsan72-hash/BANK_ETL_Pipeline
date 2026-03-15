# dashboard/app.py

import sqlite3
from pathlib import Path
from datetime import date

import pandas as pd
import streamlit as st

# ─────────────────────────────────────────────────────────────
# Path Resolution — search multiple candidate locations
# ─────────────────────────────────────────────────────────────

def find_db() -> Path:
    """
    Search for bank_warehouse.db across all likely locations.
    Returns the first path that exists.
    Raises FileNotFoundError if none found.
    """
    candidates = [
        # Relative to this file's location (most reliable)
        Path(__file__).resolve().parent.parent / "warehouse" / "bank_warehouse.db",
        # Relative to current working directory
        Path("warehouse") / "bank_warehouse.db",
        Path("../warehouse") / "bank_warehouse.db",
        # Absolute fallback — update this if your project is elsewhere
        Path(r"D:\BANK_ETL_Pipeline\warehouse\bank_warehouse.db"),
    ]
    for p in candidates:
        if p.exists():
            return p.resolve()
    raise FileNotFoundError(
        "bank_warehouse.db not found. Searched:\n" +
        "\n".join(f"  {p}" for p in candidates)
    )


try:
    DB_PATH = find_db()
except FileNotFoundError as _e:
    DB_PATH = None
    _db_error = str(_e)
else:
    _db_error = None


# ─────────────────────────────────────────────────────────────
# Data Loading
# ─────────────────────────────────────────────────────────────

@st.cache_data
def load_data() -> pd.DataFrame:
    """
    Load all fact + dimension data from the SQLite warehouse.
    Returns an empty DataFrame if the warehouse has no data yet.
    """
    if DB_PATH is None or not DB_PATH.exists():
        return pd.DataFrame()

    conn = sqlite3.connect(DB_PATH)
    df   = pd.read_sql(
        """
        SELECT
            f.transaction_id,
            f.amount,
            f.balance,
            f.description,
            d.date,
            d.year,
            d.month,
            d.quarter,
            c.customer_id,
            c.region,
            c.age,
            c.sex,
            t.transaction_type
        FROM fact_transactions        f
        JOIN dim_date             d ON f.date_sk            = d.date_id
        JOIN dim_customer         c ON f.customer_sk         = c.customer_sk
        JOIN dim_transaction_type t ON f.transaction_type_sk = t.transaction_type_sk
        """,
        conn,
    )
    conn.close()

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    nat_count  = df["date"].isna().sum()
    if nat_count > 0:
        df = df.dropna(subset=["date"])

    return df


@st.cache_data
def load_audit() -> pd.DataFrame:
    """Load the 20 most recent audit_load rows."""
    if DB_PATH is None or not DB_PATH.exists():
        return pd.DataFrame()

    conn  = sqlite3.connect(DB_PATH)
    audit = pd.read_sql(
        """
        SELECT run_id, run_timestamp, source_table, source_count,
               target_table, target_count, duration_seconds, notes
        FROM   audit_load
        ORDER  BY run_timestamp DESC
        LIMIT  20
        """,
        conn,
    )
    conn.close()
    return audit


# ─────────────────────────────────────────────────────────────
# Helper Utilities
# ─────────────────────────────────────────────────────────────

def safe_date_range(df: pd.DataFrame):
    """
    Return (min_date, max_date) as Python date objects.
    Falls back to today if df is empty or all dates are NaT.
    """
    today = date.today()
    if df.empty or "date" not in df.columns:
        return today, today
    valid = df["date"].dropna()
    if valid.empty:
        return today, today
    return valid.min().date(), valid.max().date()


def fmt_currency(value: float) -> str:
    return f"£{value:,.2f}"


def fmt_count(value: int) -> str:
    return f"{value:,}"


# ─────────────────────────────────────────────────────────────
# Page Config
# ─────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Bank ETL Dashboard",
    page_icon="🏦",
    layout="wide",
)

st.title("🏦 Bank ETL Pipeline Dashboard")

# ─────────────────────────────────────────────────────────────
# DB Path Error — show clear diagnostic and stop
# ─────────────────────────────────────────────────────────────

if DB_PATH is None:
    st.error("❌ Could not locate the warehouse database.")
    st.code(_db_error)
    st.info(
        "**How to fix:**\n\n"
        "1. Make sure the pipeline has run: `python run.py`\n"
        "2. Confirm `warehouse/bank_warehouse.db` exists in your project root.\n"
        "3. If your project is not at `D:\\BANK_ETL_Pipeline`, "
        "update the path in `find_db()` inside `dashboard/app.py`."
    )
    st.stop()

# ─────────────────────────────────────────────────────────────
# Load Data
# ─────────────────────────────────────────────────────────────

df = load_data()

if df.empty:
    st.error(
        f"⚠️ Database found at `{DB_PATH}` but returned no rows.\n\n"
        "Run the pipeline to populate the warehouse:\n"
        "```\npython run.py\n```"
    )
    st.stop()

# ─────────────────────────────────────────────────────────────
# Sidebar — Filters
# ─────────────────────────────────────────────────────────────

with st.sidebar:
    st.header("⚙️ Filters")
    st.caption(f"✅ DB: `{DB_PATH.name}`")
    st.caption(f"📦 {fmt_count(len(df))} total rows")

    # Date range
    min_date, max_date = safe_date_range(df)
    date_range = st.date_input(
        "Date Range",
        value=[min_date, max_date],
        min_value=min_date,
        max_value=max_date,
    )

    # Region
    regions = ["All"] + sorted(df["region"].dropna().unique().tolist())
    region  = st.selectbox("Region", regions)

    # Transaction type
    all_types = sorted(df["transaction_type"].dropna().unique().tolist())
    tx_types  = st.multiselect(
        "Transaction Type",
        options=all_types,
        default=all_types,
    )

    st.divider()

    if st.button("🔄 Refresh Data"):
        st.cache_data.clear()
        st.rerun()

# ─────────────────────────────────────────────────────────────
# Apply Filters
# ─────────────────────────────────────────────────────────────

filt = df.copy()

if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
    filt = filt[
        (filt["date"] >= pd.Timestamp(date_range[0])) &
        (filt["date"] <= pd.Timestamp(date_range[1]))
    ]

if region != "All":
    filt = filt[filt["region"] == region]

if tx_types:
    filt = filt[filt["transaction_type"].isin(tx_types)]

# ─────────────────────────────────────────────────────────────
# KPI Cards
# ─────────────────────────────────────────────────────────────

st.subheader("📊 Key Metrics")

k1, k2, k3, k4 = st.columns(4)
k1.metric("Total Transactions", fmt_count(len(filt)))
k2.metric("Total Volume",       fmt_currency(filt["amount"].sum()))
k3.metric("Unique Customers",   fmt_count(filt["customer_id"].nunique()))
k4.metric("Avg Transaction",    fmt_currency(filt["amount"].mean()) if not filt.empty else "£0.00")

st.divider()

# ─────────────────────────────────────────────────────────────
# Charts — Row 1
# ─────────────────────────────────────────────────────────────

col_a, col_b = st.columns(2)

with col_a:
    st.subheader("📈 Monthly Transaction Volume")
    if not filt.empty:
        monthly = (
            filt.groupby(filt["date"].dt.to_period("M"))["amount"]
            .sum().reset_index()
        )
        monthly["date"] = monthly["date"].astype(str)
        st.line_chart(monthly.set_index("date")["amount"])
    else:
        st.info("No data for selected filters.")

with col_b:
    st.subheader("📊 Transaction Type Distribution")
    if not filt.empty:
        st.bar_chart(filt["transaction_type"].value_counts())
    else:
        st.info("No data for selected filters.")

# ─────────────────────────────────────────────────────────────
# Charts — Row 2
# ─────────────────────────────────────────────────────────────

col_c, col_d = st.columns(2)

with col_c:
    st.subheader("🌍 Volume by Region")
    if not filt.empty:
        st.bar_chart(
            filt.groupby("region")["amount"]
            .sum().sort_values(ascending=False)
        )
    else:
        st.info("No data for selected filters.")

with col_d:
    st.subheader("🔢 Monthly Transaction Count")
    if not filt.empty:
        monthly_count = (
            filt.groupby(filt["date"].dt.to_period("M"))["transaction_id"]
            .count().reset_index()
        )
        monthly_count["date"] = monthly_count["date"].astype(str)
        st.bar_chart(monthly_count.set_index("date")["transaction_id"])
    else:
        st.info("No data for selected filters.")

st.divider()

# ─────────────────────────────────────────────────────────────
# Top 10 Customers Table
# ─────────────────────────────────────────────────────────────

st.subheader("🏆 Top 10 Customers by Volume")

if not filt.empty:
    top = (
        filt.groupby("customer_id")
        .agg(
            total_volume       =("amount",         "sum"),
            total_transactions =("transaction_id",  "count"),
            avg_amount         =("amount",         "mean"),
        )
        .reindex(columns=["total_volume","total_transactions","avg_amount"])
        .sort_values("total_volume", key=abs, ascending=False)
        .head(10)
        .reset_index()
    )
    top.columns = ["Customer ID", "Total Volume (£)",
                   "Transactions", "Avg Amount (£)"]
    top["Total Volume (£)"] = top["Total Volume (£)"].round(2)
    top["Avg Amount (£)"]   = top["Avg Amount (£)"].round(2)
    st.dataframe(top, use_container_width=True, hide_index=True)
else:
    st.info("No data for selected filters.")

st.divider()

# ─────────────────────────────────────────────────────────────
# Data Quality — Audit Log
# ─────────────────────────────────────────────────────────────

st.subheader("🔍 Data Quality — Audit Log")

audit_df = load_audit()

if not audit_df.empty:
    a1, a2, a3 = st.columns(3)

    fact_rows = audit_df[
        audit_df["target_table"] == "fact_transactions"
    ]["target_count"].max()

    a1.metric("Last Pipeline Run",  str(audit_df["run_timestamp"].iloc[0])[:19])
    a2.metric("Fact Rows in Table", fmt_count(int(fact_rows)) if pd.notna(fact_rows) else "—")
    a3.metric("Audit Records",      fmt_count(len(audit_df)))

    st.dataframe(audit_df, use_container_width=True, hide_index=True)
else:
    st.info("No audit records found.")

# ─────────────────────────────────────────────────────────────
# Raw Data Explorer
# ─────────────────────────────────────────────────────────────

with st.expander("🔎 Raw Data Explorer", expanded=False):
    st.caption(
        f"Showing {min(len(filt), 500):,} of "
        f"{len(filt):,} rows (capped at 500)"
    )
    st.dataframe(
        filt.head(500).reset_index(drop=True),
        use_container_width=True,
    )