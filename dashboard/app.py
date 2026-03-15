# dashboard/app.py

import sqlite3
from pathlib import Path
from datetime import date, datetime

import pandas as pd
import streamlit as st

# ─────────────────────────────────────────────────────────────
# Path Resolution
# ─────────────────────────────────────────────────────────────

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH      = PROJECT_ROOT / "warehouse" / "bank_warehouse.db"

# Fallback search if the above does not exist
if not DB_PATH.exists():
    candidates = [
        Path("warehouse") / "bank_warehouse.db",
        Path("../warehouse") / "bank_warehouse.db",
        Path(r"D:\BANK_ETL_Pipeline\warehouse\bank_warehouse.db"),
    ]
    for p in candidates:
        if p.exists():
            DB_PATH = p.resolve()
            break


# ─────────────────────────────────────────────────────────────
# Data Loaders
# ─────────────────────────────────────────────────────────────

def _conn():
    return sqlite3.connect(DB_PATH)


@st.cache_data(ttl=60)
def load_customers() -> pd.DataFrame:
    """Load all dim_customer rows."""
    conn = _conn()
    df = pd.read_sql("SELECT * FROM dim_customer ORDER BY customer_sk", conn)
    conn.close()
    return df


@st.cache_data(ttl=60)
def load_transactions() -> pd.DataFrame:
    """Load joined fact + dimension data."""
    conn = _conn()
    df = pd.read_sql(
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
    df = df.dropna(subset=["date"])
    return df


@st.cache_data(ttl=60)
def load_audit() -> pd.DataFrame:
    """Load audit_load table."""
    conn = _conn()
    df = pd.read_sql(
        """
        SELECT run_id, run_timestamp, source_table, source_count,
               target_table, target_count, duration_seconds, notes
        FROM   audit_load
        ORDER  BY run_timestamp ASC
        """,
        conn,
    )
    conn.close()
    df["run_timestamp"] = pd.to_datetime(df["run_timestamp"], errors="coerce")
    return df


@st.cache_data(ttl=60)
def null_counts_customers() -> pd.DataFrame:
    """Return per-column NULL counts for dim_customer."""
    conn  = _conn()
    cols  = [r[1] for r in conn.execute("PRAGMA table_info(dim_customer)").fetchall()]
    total = conn.execute("SELECT COUNT(*) FROM dim_customer").fetchone()[0]
    rows  = []
    for col in cols:
        nulls = conn.execute(
            f"SELECT COUNT(*) FROM dim_customer WHERE {col} IS NULL"
        ).fetchone()[0]
        rows.append({
            "Column":    col,
            "Null Count": nulls,
            "Valid Count": total - nulls,
            "Null %":    round(nulls / total * 100, 1) if total else 0,
        })
    conn.close()
    return pd.DataFrame(rows)


@st.cache_data(ttl=60)
def null_counts_transactions() -> pd.DataFrame:
    """Return per-column NULL counts for fact_transactions."""
    conn  = _conn()
    cols  = [r[1] for r in conn.execute("PRAGMA table_info(fact_transactions)").fetchall()]
    total = conn.execute("SELECT COUNT(*) FROM fact_transactions").fetchone()[0]
    rows  = []
    for col in cols:
        nulls = conn.execute(
            f"SELECT COUNT(*) FROM fact_transactions WHERE {col} IS NULL"
        ).fetchone()[0]
        rows.append({
            "Column":     col,
            "Null Count":  nulls,
            "Valid Count": total - nulls,
            "Null %":     round(nulls / total * 100, 1) if total else 0,
        })
    conn.close()
    return pd.DataFrame(rows)


# ─────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────

def safe_date_range(df: pd.DataFrame):
    today = date.today()
    if df.empty or "date" not in df.columns:
        return today, today
    valid = df["date"].dropna()
    if valid.empty:
        return today, today
    return valid.min().date(), valid.max().date()


def fmt_c(v):  return f"£{v:,.2f}"
def fmt_n(v):  return f"{int(v):,}"
def fmt_s(v):  return f"{v:.3f}s"


# ─────────────────────────────────────────────────────────────
# Page Setup
# ─────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Bank ETL Dashboard",
    page_icon="🏦",
    layout="wide",
)

# Custom CSS — clean professional style
st.markdown("""
<style>
[data-testid="metric-container"] {
    background: #f8f9fb;
    border: 1px solid #e8eaed;
    border-radius: 10px;
    padding: 14px 18px;
}
[data-testid="metric-container"] label {
    font-size: 12px !important;
    color: #6b7280 !important;
    text-transform: uppercase;
    letter-spacing: .05em;
}
[data-testid="metric-container"] [data-testid="stMetricValue"] {
    font-size: 24px !important;
    font-weight: 700 !important;
    color: #111827 !important;
}
div[data-testid="stTabs"] button { font-size: 14px; font-weight: 500; }
</style>
""", unsafe_allow_html=True)

st.title("🏦 Bank ETL Pipeline Dashboard")

# ─────────────────────────────────────────────────────────────
# DB Guard
# ─────────────────────────────────────────────────────────────

if not DB_PATH.exists():
    st.error(f"❌ Database not found at: `{DB_PATH}`\n\nRun: `python run.py`")
    st.stop()

# ─────────────────────────────────────────────────────────────
# Load All Data
# ─────────────────────────────────────────────────────────────

cust_df   = load_customers()
trans_df  = load_transactions()
audit_df  = load_audit()
null_cust = null_counts_customers()
null_fact = null_counts_transactions()

has_transactions = not trans_df.empty

# ─────────────────────────────────────────────────────────────
# Sidebar
# ─────────────────────────────────────────────────────────────

with st.sidebar:
    st.header("⚙️ Filters")
    st.caption(f"✅ `{DB_PATH.name}`")

    # Transactions filter (only shown if data exists)
    if has_transactions:
        min_d, max_d = safe_date_range(trans_df)
        date_range   = st.date_input(
            "Date Range", value=[min_d, max_d],
            min_value=min_d, max_value=max_d,
        )
        regions   = ["All"] + sorted(trans_df["region"].dropna().unique().tolist())
        region    = st.selectbox("Region", regions)
        all_types = sorted(trans_df["transaction_type"].dropna().unique().tolist())
        tx_types  = st.multiselect("Transaction Type", all_types, default=all_types)
    else:
        date_range = None
        region     = "All"
        tx_types   = []

    st.divider()
    if st.button("🔄 Refresh"):
        st.cache_data.clear()
        st.rerun()

# Apply transaction filters
if has_transactions:
    filt = trans_df.copy()
    if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
        filt = filt[
            (filt["date"] >= pd.Timestamp(date_range[0])) &
            (filt["date"] <= pd.Timestamp(date_range[1]))
        ]
    if region != "All":
        filt = filt[filt["region"] == region]
    if tx_types:
        filt = filt[filt["transaction_type"].isin(tx_types)]
else:
    filt = pd.DataFrame()

# ─────────────────────────────────────────────────────────────
# TOP-LEVEL KPIs
# ─────────────────────────────────────────────────────────────

st.subheader("📊 Overview")

c1, c2, c3, c4, c5 = st.columns(5)

# Total customers loaded
c1.metric("Total Customers",     fmt_n(len(cust_df)))

# Customers with at least one NULL field
cust_null_rows = null_cust[null_cust["Null Count"] > 0]["Null Count"].sum()
c2.metric("Customer NULL Fields", fmt_n(int(cust_null_rows)),
          help="Total NULL values across all customer columns")

# Transactions
c3.metric("Total Transactions",
          fmt_n(len(filt)) if has_transactions else "—")

# Total pipeline stages run
c4.metric("Pipeline Runs",       fmt_n(len(audit_df)))

# Total pipeline duration
total_dur = audit_df["duration_seconds"].sum() if not audit_df.empty else 0
c5.metric("Total Pipeline Time", fmt_s(total_dur))

st.divider()

# ─────────────────────────────────────────────────────────────
# TABS
# ─────────────────────────────────────────────────────────────

tab1, tab2, tab3, tab4 = st.tabs([
    "👥 Customers",
    "⚠️ Data Quality (NULLs)",
    "⏱️ Pipeline Timing",
    "💳 Transactions",
])


# ══════════════════════════════════════════════════════════════
# TAB 1 — CUSTOMERS
# ══════════════════════════════════════════════════════════════

with tab1:
    st.subheader("Customer Summary")

    # KPIs
    k1, k2, k3, k4 = st.columns(4)

    k1.metric("Total Customers Loaded", fmt_n(len(cust_df)))

    # Added in latest run
    if not audit_df.empty:
        latest = audit_df[audit_df["target_table"] == "dim_customer"].iloc[-1]
        k2.metric(
            "Latest Load Count",
            fmt_n(int(latest["source_count"])),
            help=f"Run at {str(latest['run_timestamp'])[:19]}",
        )
        k3.metric(
            "Latest Load Time",
            fmt_s(latest["duration_seconds"]),
        )
    else:
        k2.metric("Latest Load Count", "—")
        k3.metric("Latest Load Time",  "—")

    # Customers with any NULL
    rows_with_null = (cust_df.isnull().any(axis=1)).sum()
    k4.metric("Customers with ≥1 NULL", fmt_n(int(rows_with_null)))

    st.divider()

    # Load history for dim_customer
    cust_audit = audit_df[audit_df["target_table"] == "dim_customer"].copy()

    if not cust_audit.empty:
        st.subheader("📅 Customer Load History")

        cust_audit["run_timestamp"] = cust_audit["run_timestamp"].astype(str).str[:19]
        cust_audit = cust_audit.rename(columns={
            "run_timestamp":  "Run Time",
            "source_count":   "Source Rows",
            "target_count":   "Table Total",
            "duration_seconds": "Duration (s)",
            "notes":          "Notes",
        })
        st.dataframe(
            cust_audit[["Run Time","Source Rows","Table Total","Duration (s)","Notes"]],
            use_container_width=True,
            hide_index=True,
        )

    st.divider()

    # Region distribution
    col_a, col_b = st.columns(2)

    with col_a:
        st.subheader("Customers by Region")
        region_counts = cust_df["region"].value_counts()
        st.bar_chart(region_counts)

    with col_b:
        st.subheader("Customers by Gender")
        sex_counts = cust_df["sex"].value_counts()
        st.bar_chart(sex_counts)

    st.divider()

    # Age distribution
    st.subheader("Age Distribution")
    age_valid = cust_df["age"].dropna()
    if not age_valid.empty:
        age_bins = pd.cut(age_valid, bins=[0,20,30,40,50,60,70,80,120],
                          labels=["<20","20-29","30-39","40-49",
                                  "50-59","60-69","70-79","80+"])
        st.bar_chart(age_bins.value_counts().sort_index())

    st.divider()

    # Full customer table
    with st.expander("🔎 Full Customer Table", expanded=False):
        st.caption(f"{len(cust_df):,} customers")
        st.dataframe(cust_df.reset_index(drop=True),
                     use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════════════════
# TAB 2 — DATA QUALITY (NULLs)
# ══════════════════════════════════════════════════════════════

with tab2:
    st.subheader("⚠️ NULL Analysis")

    # Summary KPIs
    q1, q2, q3, q4 = st.columns(4)

    total_cust_cells  = len(cust_df) * (len(cust_df.columns))
    total_cust_nulls  = int(cust_df.isnull().sum().sum())
    total_fact_cells  = null_fact["Null Count"].sum() + null_fact["Valid Count"].sum()
    total_fact_nulls  = int(null_fact["Null Count"].sum())

    q1.metric("Customer NULL Cells",
              fmt_n(total_cust_nulls),
              f"{round(total_cust_nulls/total_cust_cells*100,1)}% of all cells")

    q2.metric("Customer Rows with NULL",
              fmt_n(int(cust_df.isnull().any(axis=1).sum())),
              f"out of {len(cust_df):,} customers")

    q3.metric("Transaction NULL Cells",
              fmt_n(total_fact_nulls))

    q4.metric("Transaction Rows with NULL",
              fmt_n(int(null_fact[null_fact["Null Count"] > 0].shape[0])),
              "columns affected")

    st.divider()

    col_l, col_r = st.columns(2)

    # ── Customer NULLs ──
    with col_l:
        st.subheader("👥 dim_customer — NULL per Column")
        nc = null_cust[null_cust["Null Count"] > 0].sort_values(
            "Null Count", ascending=False)

        if nc.empty:
            st.success("✅ No NULLs found in customer data.")
        else:
            # Visual bar
            st.bar_chart(nc.set_index("Column")["Null Count"])

            # Styled table
            st.dataframe(
                nc[["Column","Null Count","Valid Count","Null %"]],
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Null %": st.column_config.ProgressColumn(
                        "Null %", min_value=0, max_value=100, format="%.1f%%"
                    )
                },
            )

    # ── Transaction NULLs ──
    with col_r:
        st.subheader("💳 fact_transactions — NULL per Column")
        nf = null_fact[null_fact["Null Count"] > 0].sort_values(
            "Null Count", ascending=False)

        if nf.empty:
            st.success("✅ No NULLs found in transaction data.")
        else:
            st.bar_chart(nf.set_index("Column")["Null Count"])
            st.dataframe(
                nf[["Column","Null Count","Valid Count","Null %"]],
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Null %": st.column_config.ProgressColumn(
                        "Null %", min_value=0, max_value=100, format="%.1f%%"
                    )
                },
            )

    st.divider()

    # All columns including zero-null ones
    with st.expander("📋 Full NULL Report — All Columns"):
        col1, col2 = st.columns(2)
        with col1:
            st.caption("dim_customer")
            st.dataframe(null_cust, use_container_width=True, hide_index=True)
        with col2:
            st.caption("fact_transactions")
            st.dataframe(null_fact, use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════════════════
# TAB 3 — PIPELINE TIMING
# ══════════════════════════════════════════════════════════════

with tab3:
    st.subheader("⏱️ Pipeline Stage Timing")

    if audit_df.empty:
        st.info("No pipeline runs recorded yet.")
    else:
        # Summary KPIs
        t1, t2, t3, t4 = st.columns(4)

        total_runs    = len(audit_df)
        total_time    = audit_df["duration_seconds"].sum()
        slowest_stage = audit_df.loc[audit_df["duration_seconds"].idxmax()]
        fastest_stage = audit_df.loc[
            audit_df[audit_df["duration_seconds"] > 0]["duration_seconds"].idxmin()
        ]

        t1.metric("Total Stages Run",    fmt_n(total_runs))
        t2.metric("Total Time",          fmt_s(total_time))
        t3.metric("Slowest Stage",
                  slowest_stage["target_table"],
                  fmt_s(slowest_stage["duration_seconds"]))
        t4.metric("Fastest Stage",
                  fastest_stage["target_table"],
                  fmt_s(fastest_stage["duration_seconds"]))

        st.divider()

        # Per-stage timing bar chart
        st.subheader("Duration by Stage")
        stage_time = (
            audit_df.groupby("target_table")["duration_seconds"]
            .sum()
            .sort_values(ascending=False)
        )
        st.bar_chart(stage_time)

        st.divider()

        # Full audit table with all columns
        st.subheader("📋 Full Audit Log")

        display_audit = audit_df.copy()
        display_audit["run_timestamp"] = display_audit["run_timestamp"].astype(str).str[:19]

        # Skipped rows extracted from notes column
        display_audit["skipped"] = (
            display_audit["notes"]
            .str.extract(r"skipped=(\d+)")
            .fillna(0)
            .astype(int)
        )

        display_audit = display_audit.rename(columns={
            "run_id":           "Run ID",
            "run_timestamp":    "Timestamp",
            "source_table":     "Source",
            "source_count":     "Source Rows",
            "target_table":     "Target Table",
            "target_count":     "Table Total",
            "duration_seconds": "Duration (s)",
            "skipped":          "Skipped",
        })

        st.dataframe(
            display_audit[[
                "Timestamp","Run ID","Source","Source Rows",
                "Target Table","Table Total","Duration (s)","Skipped"
            ]],
            use_container_width=True,
            hide_index=True,
            column_config={
                "Duration (s)": st.column_config.NumberColumn(
                    "Duration (s)", format="%.4f"
                ),
                "Skipped": st.column_config.NumberColumn(
                    "Skipped", help="Rows skipped due to missing FK"
                ),
            },
        )

        st.divider()

        # Source count vs target count reconciliation
        st.subheader("🔁 Load Reconciliation (Source vs Loaded)")
        recon = audit_df[["target_table","source_count","target_count"]].copy()
        recon["difference"] = recon["target_count"] - recon["source_count"]
        recon = recon.rename(columns={
            "target_table":  "Table",
            "source_count":  "Source Rows",
            "target_count":  "Table Total",
            "difference":    "Difference",
        })
        st.dataframe(recon, use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════════════════
# TAB 4 — TRANSACTIONS
# ══════════════════════════════════════════════════════════════

with tab4:
    if not has_transactions:
        st.info("ℹ️ No transaction data in the warehouse yet. Run the pipeline first.")
    else:
        st.subheader("💳 Transaction Analysis")

        # KPIs
        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("Filtered Rows",       fmt_n(len(filt)))
        m2.metric("Total Volume",        fmt_c(filt["amount"].sum()))
        m3.metric("Unique Customers",    fmt_n(filt["customer_id"].nunique()))
        m4.metric("Avg Transaction",     fmt_c(filt["amount"].mean()) if not filt.empty else "£0.00")
        m5.metric("Date Range",
                  f"{filt['date'].min().date()} → {filt['date'].max().date()}"
                  if not filt.empty else "—")

        st.divider()

        # ── Row 1: Monthly volume + Type distribution ──
        col_a, col_b = st.columns(2)

        with col_a:
            st.subheader("📈 Monthly Volume (£)")
            if not filt.empty:
                monthly = (
                    filt.groupby(filt["date"].dt.to_period("M"))["amount"]
                    .sum().reset_index()
                )
                monthly["date"] = monthly["date"].astype(str)
                st.line_chart(monthly.set_index("date")["amount"])
            else:
                st.info("No data.")

        with col_b:
            st.subheader("📊 Transaction Type Distribution")
            if not filt.empty:
                st.bar_chart(filt["transaction_type"].value_counts())
            else:
                st.info("No data.")

        st.divider()

        # ── Row 2: Region volume + Monthly count ──
        col_c, col_d = st.columns(2)

        with col_c:
            st.subheader("🌍 Volume by Region (£)")
            if not filt.empty:
                by_region = (
                    filt.groupby("region")["amount"]
                    .sum().sort_values(ascending=False)
                )
                st.bar_chart(by_region)
            else:
                st.info("No data.")

        with col_d:
            st.subheader("🔢 Monthly Transaction Count")
            if not filt.empty:
                mc = (
                    filt.groupby(filt["date"].dt.to_period("M"))["transaction_id"]
                    .count().reset_index()
                )
                mc["date"] = mc["date"].astype(str)
                st.bar_chart(mc.set_index("date")["transaction_id"])
            else:
                st.info("No data.")

        st.divider()

        # ── Top 10 customers ──
        st.subheader("🏆 Top 10 Customers by Volume")
        if not filt.empty:
            top = (
                filt.groupby("customer_id")
                .agg(
                    total_volume       =("amount",        "sum"),
                    total_transactions =("transaction_id", "count"),
                    avg_amount         =("amount",        "mean"),
                )
                .sort_values("total_volume", key=abs, ascending=False)
                .head(10)
                .reset_index()
            )
            top.columns = ["Customer ID","Total Volume (£)","Transactions","Avg (£)"]
            top["Total Volume (£)"] = top["Total Volume (£)"].round(2)
            top["Avg (£)"]          = top["Avg (£)"].round(2)
            st.dataframe(top, use_container_width=True, hide_index=True)

        st.divider()

        # ── Skipped / failed transactions from audit ──
        fact_audit = audit_df[audit_df["target_table"] == "fact_transactions"]
        if not fact_audit.empty:
            last_fact = fact_audit.iloc[-1]
            skipped   = 0
            if pd.notna(last_fact.get("notes")):
                import re
                m = re.search(r"skipped=(\d+)", str(last_fact["notes"]))
                if m:
                    skipped = int(m.group(1))

            s1, s2, s3 = st.columns(3)
            s1.metric("Source Rows (last run)",  fmt_n(int(last_fact["source_count"])))
            s2.metric("Loaded to Warehouse",     fmt_n(int(last_fact["target_count"])))
            s3.metric("Skipped (FK mismatch)",   fmt_n(skipped),
                      delta=f"-{skipped}" if skipped else None,
                      delta_color="inverse")

        # ── Raw data explorer ──
        with st.expander("🔎 Raw Transaction Data", expanded=False):
            st.caption(f"Showing {min(len(filt), 1000):,} of {len(filt):,} rows")
            st.dataframe(
                filt.head(1000).reset_index(drop=True),
                use_container_width=True,
            )