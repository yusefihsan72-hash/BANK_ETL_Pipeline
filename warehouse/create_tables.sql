PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS dim_date (
  date_id INTEGER PRIMARY KEY,
  date DATE NOT NULL UNIQUE,
  year INTEGER NOT NULL, quarter INTEGER NOT NULL,
  month INTEGER NOT NULL, day INTEGER NOT NULL,
  day_of_week INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS dim_customer (
  customer_sk INTEGER PRIMARY KEY,
  customer_id TEXT NOT NULL UNIQUE,
  age INTEGER, sex TEXT, region TEXT, income REAL,
  married BOOLEAN, children INTEGER, car BOOLEAN,
  save_act REAL, current_act REAL, mortgage BOOLEAN, pep BOOLEAN
);

CREATE TABLE IF NOT EXISTS dim_transaction_type (
  transaction_type_sk INTEGER PRIMARY KEY,
  transaction_type TEXT NOT NULL UNIQUE,
  category TEXT, direction TEXT
);

CREATE TABLE IF NOT EXISTS dim_account_profile (
  account_profile_sk INTEGER PRIMARY KEY,
  customer_id TEXT NOT NULL, mortgage BOOLEAN, pep BOOLEAN, car BOOLEAN,
  UNIQUE (customer_id, mortgage, pep, car)
);

CREATE TABLE IF NOT EXISTS fact_transactions (
  transaction_sk INTEGER PRIMARY KEY,
  transaction_id TEXT NOT NULL UNIQUE,
  customer_sk INTEGER NOT NULL, date_sk INTEGER NOT NULL,
  transaction_type_sk INTEGER NOT NULL, account_profile_sk INTEGER NOT NULL,
  amount REAL, balance REAL, description TEXT,
  FOREIGN KEY (customer_sk) REFERENCES dim_customer(customer_sk),
  FOREIGN KEY (date_sk) REFERENCES dim_date(date_id),
  FOREIGN KEY (transaction_type_sk) REFERENCES dim_transaction_type(transaction_type_sk),
  FOREIGN KEY (account_profile_sk) REFERENCES dim_account_profile(account_profile_sk)
);

CREATE TABLE IF NOT EXISTS audit_load (
  load_id INTEGER PRIMARY KEY, run_id TEXT NOT NULL,
  run_timestamp DATETIME NOT NULL, source_table TEXT NOT NULL,
  source_count INTEGER, target_table TEXT NOT NULL,
  target_count INTEGER, duration_seconds REAL, notes TEXT
);