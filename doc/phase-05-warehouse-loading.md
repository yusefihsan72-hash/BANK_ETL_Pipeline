# Phase 5: Warehouse and Loading

## 1. Purpose
This phase implements a SQLite data warehouse in a star schema and loads validated customer and transaction data into dimension and fact tables. It includes auditing and reconciliation to ensure completeness and data integrity.

## 2. Objectives
- Implement a star schema in SQLite suitable for analytics.
- Load cleaned and validated data into dimension tables first, then into the fact table.
- Maintain surrogate keys and enforce referential integrity.
- Capture audit data for load runs and reconciliation.

## 3. Scope
- Create SQL DDL for warehouse tables.
- Implement Python loader to upsert dimensions and load facts.
- Implement a lightweight audit system for each load.
- Provide verification queries and record count reconciliation.

## 4. Inputs Required
- Validated DataFrames for customers and transactions (from Phase 4).
- `config/config.yaml` specifying SQLite warehouse path.
- `warehouse/create_tables.sql` containing DDL.

## 5. Detailed Step-by-Step Implementation

### 5.1 Define the Star Schema and Grain

#### 5.1.1 Grain Definitions
- **fact_transactions**: one row per transaction (measures: amount, balance, etc.).
- **dim_customer**: one row per customer (customer attributes).
- **dim_date**: one row per date (calendar attributes) for transactions.
- **dim_transaction_type**: one row per distinct transaction type (category, direction).
- **dim_account_profile**: one row per account profile snapshot (mortgage, car, pep, etc.).

### 5.2 Create `warehouse/create_tables.sql`
1. Create the file and define DDL for each table.
2. Include `IF NOT EXISTS` for idempotent creation.

Example schema:
```sql
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS dim_date (
  date_id INTEGER PRIMARY KEY,
  date DATE NOT NULL UNIQUE,
  year INTEGER NOT NULL,
  quarter INTEGER NOT NULL,
  month INTEGER NOT NULL,
  day INTEGER NOT NULL,
  day_of_week INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS dim_customer (
  customer_sk INTEGER PRIMARY KEY,
  customer_id TEXT NOT NULL UNIQUE,
  age INTEGER,
  sex TEXT,
  region TEXT,
  income REAL,
  married BOOLEAN,
  children INTEGER,
  car BOOLEAN,
  save_act REAL,
  current_act REAL,
  mortgage BOOLEAN,
  pep BOOLEAN
);

CREATE TABLE IF NOT EXISTS dim_transaction_type (
  transaction_type_sk INTEGER PRIMARY KEY,
  transaction_type TEXT NOT NULL UNIQUE,
  category TEXT,
  direction TEXT
);

CREATE TABLE IF NOT EXISTS dim_account_profile (
  account_profile_sk INTEGER PRIMARY KEY,
  customer_id TEXT NOT NULL,
  mortgage BOOLEAN,
  pep BOOLEAN,
  car BOOLEAN,
  UNIQUE (customer_id, mortgage, pep, car)
);

CREATE TABLE IF NOT EXISTS fact_transactions (
  transaction_sk INTEGER PRIMARY KEY,
  transaction_id TEXT NOT NULL UNIQUE,
  customer_sk INTEGER NOT NULL,
  date_sk INTEGER NOT NULL,
  transaction_type_sk INTEGER NOT NULL,
  account_profile_sk INTEGER NOT NULL,
  amount REAL,
  balance REAL,
  description TEXT,
  FOREIGN KEY (customer_sk) REFERENCES dim_customer(customer_sk),
  FOREIGN KEY (date_sk) REFERENCES dim_date(date_id),
  FOREIGN KEY (transaction_type_sk) REFERENCES dim_transaction_type(transaction_type_sk),
  FOREIGN KEY (account_profile_sk) REFERENCES dim_account_profile(account_profile_sk)
);

CREATE TABLE IF NOT EXISTS audit_load (
  load_id INTEGER PRIMARY KEY,
  run_id TEXT NOT NULL,
  run_timestamp DATETIME NOT NULL,
  source_table TEXT NOT NULL,
  source_count INTEGER,
  target_table TEXT NOT NULL,
  target_count INTEGER,
  duration_seconds REAL,
  notes TEXT
);
```

### 5.3 Implement Loader Module (`loading/loader.py`)
1. Create `loading/__init__.py` and `loading/loader.py`.
2. Define a `WarehouseLoader` class with methods:
   - `connect()` (create SQLite connection)
   - `create_tables()` (execute `create_tables.sql`)
   - `load_dim_customer(df)`
   - `load_dim_date(df)`
   - `load_dim_transaction_type(df)`
   - `load_dim_account_profile(df)`
   - `load_fact_transactions(df)`
   - `record_audit(run_id, source_table, source_count, target_table, target_count, duration, notes)`
3. Use SQLAlchemy or `sqlite3` for DB operations. Use parameterized queries to avoid SQL injection.

#### 5.3.1 Surrogate Key Strategy
- Use SQLite `INTEGER PRIMARY KEY` for surrogate keys (auto-increment).
- For dimensions, implement upsert behavior (insert unless exists).
  - Use `INSERT OR IGNORE` for unique keys, then query the `rowid`.
- For account profile, treat composite uniqueness as the natural key.

Example upsert pattern:
```sql
INSERT OR IGNORE INTO dim_customer (customer_id, age, sex, region, income, married, children, car, save_act, current_act, mortgage, pep)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
SELECT customer_sk FROM dim_customer WHERE customer_id = ?;
```

#### 5.3.2 Dimension-First Loading Sequence
1. Load `dim_date` based on transaction dates extracted from the transactions DataFrame.
2. Load `dim_customer` from customer DataFrame.
3. Load `dim_transaction_type` from transaction types present in transactions.
4. Load `dim_account_profile` from customer profile fields.

#### 5.3.3 Fact Table Loading
1. For each transaction row:
   - Lookup `customer_sk` by `customer_id`.
   - Lookup `date_sk` by transaction date.
   - Lookup `transaction_type_sk` by transaction type.
   - Lookup `account_profile_sk` by (`customer_id`, `mortgage`, `pep`, `car`).
2. Insert into `fact_transactions` using those surrogate keys.
3. Use `INSERT OR IGNORE`/`INSERT OR REPLACE` depending on chosen strategy.

### 5.4 Upsert and Duplicate Prevention
- Use unique constraints on natural keys (e.g., `customer_id`, `transaction_id`) to prevent duplicates.
- For fact table, treat `transaction_id` as unique and use `INSERT OR IGNORE` or `INSERT OR REPLACE` for updates.
- Optionally, implement a checksum column on fact records to detect changes and update.

### 5.5 Audit Logging and Reconciliation
1. Implement `audit_load` table (see DDL).
2. At the end of each load step, record:
   - `run_id`: UUID or timestamp.
   - `run_timestamp`: current datetime.
   - `source_table`: logical source (e.g., `customer`, `transactions`).
   - `source_count`: number of source rows.
   - `target_table`: warehouse table loaded (e.g., `dim_customer`).
   - `target_count`: number of rows inserted/updated.
   - `duration_seconds`: load time.
   - `notes`: any warnings (e.g., duplicates skipped).
3. Implement reconciliation queries such as:
   - Compare source row count vs `target_count` for each load.
   - Identify missing foreign keys (e.g., transactions with no customer).

### 5.6 Verification Queries
1. Provide a set of SQL queries in `warehouse/verification_queries.sql` or in the loader module.
2. Examples:
   - `SELECT COUNT(*) FROM fact_transactions;`
   - `SELECT COUNT(*) FROM dim_customer;`
   - `SELECT COUNT(*) FROM fact_transactions WHERE customer_sk IS NULL;` (should be 0)
   - `SELECT transaction_type, COUNT(*) FROM fact_transactions GROUP BY transaction_type_sk;`

### 5.7 Folder/File Responsibilities
- `warehouse/create_tables.sql`: DDL for warehouse schema.
- `loading/loader.py`: Load logic, surrogate key management, audit logging.
- `loading/utils.py`: Helper functions for upserts, key lookups.
- `warehouse/verification_queries.sql`: Optional verification queries.
- `logs/`: Logs for load executions.

## 6. Outputs / Deliverables
- A working SQLite warehouse database file (`warehouse/bank_warehouse.db`).
- Implemented star schema in SQLite.
- Loader module that ingests validated data into dimensions and fact.
- Audit table capturing load metrics.
- Reconciliation summary output.

## 7. Dependencies
- SQLite (via Python `sqlite3` or SQLAlchemy).
- Validated DataFrames from Phase 4.
- `config/config.yaml` with warehouse path.

## 8. Risks and Mitigations
- **Risk:** Surrogate key mismatches cause FK errors.  
  **Mitigation:** Load dimensions first; validate lookups before inserting facts.

- **Risk:** Duplicate source rows cause inflation.  
  **Mitigation:** Enforce unique constraints and use upsert patterns.

- **Risk:** Long-running insert operations on large datasets.  
  **Mitigation:** Use transactions and batch inserts.

## 9. Acceptance Criteria
- The warehouse schema exists and can be created via `warehouse/create_tables.sql`.
- Dimensions load successfully and keys are generated.
- Fact table loads transactions with correct foreign keys.
- Audit table records load metrics and supports reconciliation.
- Verification queries return expected results (e.g., no null FKs).

## 10. Definition of Done
- `warehouse/bank_warehouse.db` is populated with the star schema and sample data.
- `loading/loader.py` supports end-to-end loading from validated DataFrames.
- Audit logs are stored in `audit_load` and include counts and duration.
- Documentation exists describing how to run the loader and validate the warehouse.
