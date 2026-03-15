# loading/loader.py

import sqlite3
import uuid
import time
import logging
from pathlib import Path
from datetime import datetime, timezone

import pandas as pd

logger = logging.getLogger(__name__)

DB_PATH    = Path("warehouse/bank_warehouse.db")
SQL_PATH   = Path("warehouse/create_tables.sql")


class WarehouseLoader:
    """
    Handles all database loading operations for the star schema warehouse.
    Load order must always be:
        dim_date → dim_customer → dim_transaction_type
        → dim_account_profile → fact_transactions
    """

    def __init__(self):
        """Connect to SQLite and create all tables if they do not exist."""
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        self.conn.execute("PRAGMA foreign_keys = ON")
        self._create_tables()
        logger.info("WarehouseLoader initialized — connected to %s", DB_PATH)

    # ─────────────────────────────────────────────────────────
    # Table Creation
    # ─────────────────────────────────────────────────────────

    def _create_tables(self) -> None:
        """Execute the DDL script to create all warehouse tables."""
        if not SQL_PATH.exists():
            raise FileNotFoundError(
                f"DDL script not found: {SQL_PATH.resolve()}"
            )
        self.conn.executescript(SQL_PATH.read_text(encoding="utf-8"))
        self.conn.commit()
        logger.info("Warehouse tables verified / created.")

    # ─────────────────────────────────────────────────────────
    # Run ID helper
    # ─────────────────────────────────────────────────────────

    @staticmethod
    def _run_id() -> str:
        """Generate a short unique run identifier."""
        return str(uuid.uuid4())[:8]

    # ─────────────────────────────────────────────────────────
    # Audit Logging
    # ─────────────────────────────────────────────────────────

    def _audit(
        self,
        source_table: str,
        source_count: int,
        target_table: str,
        target_count: int,
        duration: float,
        notes: str = "",
    ) -> None:
        """
        Insert one row into audit_load after every load operation.

        Args:
            source_table:  Logical source name (e.g. 'customer').
            source_count:  Number of input rows.
            target_table:  Warehouse table name (e.g. 'dim_customer').
            target_count:  Number of rows currently in the target table.
            duration:      Elapsed seconds for the load step.
            notes:         Optional notes or warnings.
        """
        self.conn.execute(
            """
            INSERT INTO audit_load
                (run_id, run_timestamp, source_table, source_count,
                 target_table, target_count, duration_seconds, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                self._run_id(),
                datetime.now(timezone.utc).isoformat(),
                source_table,
                source_count,
                target_table,
                target_count,
                round(duration, 4),
                notes,
            ),
        )
        self.conn.commit()

    # ─────────────────────────────────────────────────────────
    # dim_customer
    # ─────────────────────────────────────────────────────────

    def load_dim_customer(self, df: pd.DataFrame) -> None:
        """
        Upsert customer records into dim_customer.
        Uses INSERT OR IGNORE so existing customer_id rows are not overwritten.

        Args:
            df: Validated customer DataFrame with standardized columns.
        """
        start = time.perf_counter()

        cols = [
            "customer_id", "age", "sex", "region", "income",
            "married", "children", "car", "save_act",
            "current_act", "mortgage", "pep",
        ]

        # Keep only columns that exist in the DataFrame
        available = [c for c in cols if c in df.columns]
        rows = [tuple(row) for row in df[available].itertuples(index=False)]

        placeholders = ", ".join(["?"] * len(available))
        col_names    = ", ".join(available)

        self.conn.executemany(
            f"INSERT OR IGNORE INTO dim_customer ({col_names}) "
            f"VALUES ({placeholders})",
            rows,
        )
        self.conn.commit()

        count    = self.conn.execute(
            "SELECT COUNT(*) FROM dim_customer").fetchone()[0]
        duration = time.perf_counter() - start

        self._audit("customer", len(df), "dim_customer", count, duration)
        logger.info("dim_customer — %d rows in table (loaded %d)", count, len(df))

    # ─────────────────────────────────────────────────────────
    # dim_date
    # ─────────────────────────────────────────────────────────

    def load_dim_date(self, df: pd.DataFrame) -> None:
        """
        Populate dim_date from all unique dates in the transaction DataFrame.
        Uses INSERT OR IGNORE — safe to call multiple times.

        Args:
            df: Validated transaction DataFrame containing a 'date' column.
        """
        start = time.perf_counter()

        if "date" not in df.columns:
            logger.warning("load_dim_date: no 'date' column found, skipping.")
            return

        dates = pd.to_datetime(df["date"], errors="coerce").dropna()
        dates = dates.dt.normalize().unique()

        rows = [
            (
                int(d.strftime("%Y%m%d")),  # date_id  e.g. 20240110
                str(d.date()),              # date     e.g. 2024-01-10
                int(d.year),
                int(d.quarter),
                int(d.month),
                int(d.day),
                int(d.dayofweek),           # 0 = Monday
            )
            for d in dates
        ]

        self.conn.executemany(
            """
            INSERT OR IGNORE INTO dim_date
                (date_id, date, year, quarter, month, day, day_of_week)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            rows,
        )
        self.conn.commit()

        count    = self.conn.execute(
            "SELECT COUNT(*) FROM dim_date").fetchone()[0]
        duration = time.perf_counter() - start

        self._audit("transactions", len(rows), "dim_date", count, duration)
        logger.info("dim_date — %d unique dates loaded", len(rows))

    # ─────────────────────────────────────────────────────────
    # dim_transaction_type
    # ─────────────────────────────────────────────────────────

    def load_dim_transaction_type(self, df: pd.DataFrame) -> None:
        """
        Populate dim_transaction_type from unique transaction_type values.
        Uses INSERT OR IGNORE — safe to call multiple times.

        Args:
            df: Validated transaction DataFrame with a 'transaction_type' column.
        """
        start = time.perf_counter()

        if "transaction_type" not in df.columns:
            logger.warning(
                "load_dim_transaction_type: no 'transaction_type' column, skipping.")
            return

        unique_types = (
            df["transaction_type"]
            .dropna()
            .astype(str)
            .str.strip()
            .unique()
        )

        rows = [(t,) for t in unique_types if t]

        self.conn.executemany(
            "INSERT OR IGNORE INTO dim_transaction_type (transaction_type) VALUES (?)",
            rows,
        )
        self.conn.commit()

        count    = self.conn.execute(
            "SELECT COUNT(*) FROM dim_transaction_type").fetchone()[0]
        duration = time.perf_counter() - start

        self._audit(
            "transactions", len(rows),
            "dim_transaction_type", count, duration
        )
        logger.info(
            "dim_transaction_type — %d types in table", count)

    # ─────────────────────────────────────────────────────────
    # dim_account_profile
    # ─────────────────────────────────────────────────────────

    def load_dim_account_profile(self, df: pd.DataFrame) -> None:
        """
        Populate dim_account_profile from unique (customer_id, mortgage, pep, car)
        combinations found in the transaction DataFrame.

        Falls back gracefully if the profile columns are absent.

        Args:
            df: Validated transaction DataFrame.
        """
        start = time.perf_counter()

        required = ["customer_id", "mortgage", "pep", "car"]
        missing  = [c for c in required if c not in df.columns]

        if missing:
            # Insert a default placeholder profile so fact FK is never NULL
            self.conn.execute(
                """
                INSERT OR IGNORE INTO dim_account_profile
                    (account_profile_sk, customer_id, mortgage, pep, car)
                VALUES (1, 'UNKNOWN', 0, 0, 0)
                """
            )
            self.conn.commit()
            logger.warning(
                "load_dim_account_profile: missing columns %s — "
                "inserted default placeholder profile.", missing
            )
            return

        profile_df = df[required].drop_duplicates()
        rows = [tuple(r) for r in profile_df.itertuples(index=False)]

        self.conn.executemany(
            """
            INSERT OR IGNORE INTO dim_account_profile
                (customer_id, mortgage, pep, car)
            VALUES (?, ?, ?, ?)
            """,
            rows,
        )
        self.conn.commit()

        count    = self.conn.execute(
            "SELECT COUNT(*) FROM dim_account_profile").fetchone()[0]
        duration = time.perf_counter() - start

        self._audit(
            "transactions", len(rows),
            "dim_account_profile", count, duration
        )
        logger.info("dim_account_profile — %d profiles in table", count)

    # ─────────────────────────────────────────────────────────
    # fact_transactions
    # ─────────────────────────────────────────────────────────

    def load_fact_transactions(self, df: pd.DataFrame) -> None:
        """
        Load validated transactions into fact_transactions.

        For each row:
            - Looks up customer_sk  from dim_customer  by customer_id.
            - Looks up date_sk      from dim_date       by date string.
            - Looks up transaction_type_sk from dim_transaction_type.
            - Uses account_profile_sk = 1 as default if profile not found.
            - Skips rows where any required FK lookup fails (logs a warning).

        Uses INSERT OR IGNORE on transaction_id to prevent duplicates.

        Args:
            df: Validated and enriched transaction DataFrame.
        """
        start  = time.perf_counter()
        cur    = self.conn.cursor()
        loaded = 0
        skipped = 0

        for _, row in df.iterrows():

            # -- FK lookups ----------------------------------------
            csk = cur.execute(
                "SELECT customer_sk FROM dim_customer WHERE customer_id = ?",
                (str(row["customer_id"]),),
            ).fetchone()

            date_str = str(pd.to_datetime(row["date"]).date()) \
                       if pd.notna(row.get("date")) else None
            dsk = cur.execute(
                "SELECT date_id FROM dim_date WHERE date = ?",
                (date_str,),
            ).fetchone() if date_str else None

            tsk = cur.execute(
                "SELECT transaction_type_sk FROM dim_transaction_type "
                "WHERE transaction_type = ?",
                (str(row.get("transaction_type", "")),),
            ).fetchone()

            # Default account profile SK = 1
            apsk = cur.execute(
                "SELECT account_profile_sk FROM dim_account_profile "
                "WHERE customer_id = ? LIMIT 1",
                (str(row["customer_id"]),),
            ).fetchone() or (1,)

            # -- Skip if any required FK is missing ----------------
            if not (csk and dsk and tsk):
                logger.warning(
                    "Skipping transaction_id=%s — FK lookup failed "
                    "(customer_sk=%s, date_sk=%s, type_sk=%s)",
                    row.get("transaction_id"), csk, dsk, tsk,
                )
                skipped += 1
                continue

            # -- Insert fact row -----------------------------------
            cur.execute(
                """
                INSERT OR IGNORE INTO fact_transactions
                    (transaction_id, customer_sk, date_sk,
                     transaction_type_sk, account_profile_sk,
                     amount, balance, description)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(row.get("transaction_id", "")),
                    csk[0],
                    dsk[0],
                    tsk[0],
                    apsk[0],
                    float(row.get("amount", 0.0)),
                    float(row.get("balance", 0.0)) if pd.notna(row.get("balance")) else None,
                    str(row.get("description", "")),
                ),
            )
            loaded += 1

        self.conn.commit()

        count    = self.conn.execute(
            "SELECT COUNT(*) FROM fact_transactions").fetchone()[0]
        duration = time.perf_counter() - start

        self._audit(
            "transactions", len(df),
            "fact_transactions", count, duration,
            notes=f"skipped={skipped}",
        )
        logger.info(
            "fact_transactions — %d loaded / %d skipped / %d total in table",
            loaded, skipped, count,
        )

    # ─────────────────────────────────────────────────────────
    # Verification Queries
    # ─────────────────────────────────────────────────────────

    def verify(self) -> dict:
        """
        Run basic row-count verification across all warehouse tables.

        Returns:
            Dictionary with table names as keys and row counts as values.
        """
        tables = [
            "dim_customer",
            "dim_date",
            "dim_transaction_type",
            "dim_account_profile",
            "fact_transactions",
            "audit_load",
        ]
        counts = {}
        for table in tables:
            counts[table] = self.conn.execute(
                f"SELECT COUNT(*) FROM {table}"
            ).fetchone()[0]

        null_fks = self.conn.execute(
            "SELECT COUNT(*) FROM fact_transactions "
            "WHERE customer_sk IS NULL OR date_sk IS NULL "
            "OR transaction_type_sk IS NULL"
        ).fetchone()[0]

        counts["fact_null_fks"] = null_fks
        logger.info("Verification: %s", counts)
        return counts