# Phase 6: Dashboard

## 1. Purpose
This phase delivers a Streamlit dashboard that connects to the SQLite warehouse, showcasing business analytics and data quality metrics through interactive KPIs, trends, and filters.

## 2. Objectives
- Build a Streamlit dashboard for business analytics and data quality visibility.
- Provide key KPIs, trend charts, top entity rankings, and filtering capabilities.

## 3. Scope
- Implement `dashboard/app.py` as the Streamlit entry point.
- Connect to `warehouse/bank_warehouse.db` and query data.
- Include KPI cards and visualizations for transaction volume, customer counts, and quality metrics.
- Provide filters for date range, region, and transaction type.
- Capture screenshots demonstrating dashboard features for reporting.

## 4. Inputs Required
- Populated SQLite warehouse (`warehouse/bank_warehouse.db`).
- Dashboard config settings (optional, in `config/config.yaml`).
- Sample data for demo purposes.

## 5. Detailed Step-by-Step Implementation

### 5.1 Set Up the Dashboard Module
1. Create `dashboard/` directory if missing.
2. Add `dashboard/app.py` as the entry point.
3. Ensure `dashboard/__init__.py` exists for module recognition.

### 5.2 Connect to SQLite Warehouse
1. Use `sqlite3` or SQLAlchemy to connect to `warehouse/bank_warehouse.db`.
2. Encapsulate connection logic in `dashboard/db.py` (optional).

Example connection helper:
```python
import sqlite3
from pathlib import Path

DB_PATH = Path("../warehouse/bank_warehouse.db")

def get_connection():
    return sqlite3.connect(DB_PATH)
```

### 5.3 Define KPI Queries
1. **Total transactions**
```sql
SELECT COUNT(*) FROM fact_transactions;
```
2. **Total volume**
```sql
SELECT SUM(amount) FROM fact_transactions;
```
3. **Customer count**
```sql
SELECT COUNT(*) FROM dim_customer;
```
4. **Data quality %** (example)
```sql
SELECT 
  (1.0 - CAST(SUM(CASE WHEN failure_reasons IS NOT NULL THEN 1 ELSE 0 END) AS FLOAT) / COUNT(*)) * 100
FROM quarantine/transactions_quarantine.csv -- this is a concept; store quality metrics in a table
```

### 5.4 Build Dashboard Layout
1. Use `st.sidebar` for filters.
2. Use top-level KPI cards for key metrics.
3. Add tabs or sections for:
   - Overview (KPIs)
   - Trends (time series)
   - Top entities (customers, transaction types)
   - Data quality (quarantine summary)

### 5.5 Implement Filters
1. Date range filter (based on `dim_date.date` or transaction dates).
2. Region filter (based on `dim_customer.region`).
3. Transaction type filter (based on `dim_transaction_type.transaction_type`).

Example filter code:
```python
start_date, end_date = st.sidebar.date_input("Date range", [default_start, default_end])
region = st.sidebar.selectbox("Region", regions_list, index=0)
transaction_type = st.sidebar.multiselect("Transaction type", transaction_types)
```

### 5.6 Visualizations
Use Streamlit and `altair`/`plotly` for charts.

#### 5.6.1 Trend Chart (Daily/Monthly)
- Query aggregated transaction volume by date.
- Render line chart (altair or streamlit built-in).

Example:
```python
query = """
SELECT d.date, SUM(f.amount) as total_amount
FROM fact_transactions f
JOIN dim_date d ON f.date_sk = d.date_id
GROUP BY d.date
ORDER BY d.date
"""
```

#### 5.6.2 Top Customers
- Query top N customers by transaction volume.

Example:
```sql
SELECT c.customer_id, SUM(f.amount) AS total_amount
FROM fact_transactions f
JOIN dim_customer c ON f.customer_sk = c.customer_sk
GROUP BY c.customer_id
ORDER BY total_amount DESC
LIMIT 10;
```

#### 5.6.3 Transaction Type Distribution
- Query count by transaction type and render pie/bar chart.

Example:
```sql
SELECT t.transaction_type, COUNT(*) as count
FROM fact_transactions f
JOIN dim_transaction_type t ON f.transaction_type_sk = t.transaction_type_sk
GROUP BY t.transaction_type;
```

#### 5.6.4 Data Quality Panel
- Query the audit table for recent load counts and compare against expected.
- If quarantine data is stored (e.g., in a table), show counts by reason.

### 5.7 Prepare Screenshots for Evaluation
Capture screenshots for:
- Dashboard Overview (KPIs + filters).
- Trend chart (time series).
- Top customers list.
- Data quality panel with quarantine metrics.

## 6. Recommended Page Structure / Layout
- **Header**: Project title, last refresh timestamp.
- **Sidebar**: Filters (date range, region, transaction type).
- **Main Panel**:
  - Row 1: KPI cards (total transactions, total volume, customers, data quality %).
  - Row 2: Trend chart (transaction volume over time).
  - Row 3: Two columns: top customers (left), transaction type distribution (right).
  - Row 4: Data quality summary (quarantine counts, recent validation failures).

## 7. SQL / Query Requirements
The dashboard relies on the warehouse schema to support:
- Time series aggregations via `dim_date`.
- Joins between fact and dimension tables (`customer_sk`, `date_sk`, etc.).
- Data quality metrics (via audit or quarantine structures).

## 8. Performance and Usability Recommendations
- Add indexes on foreign keys if using larger datasets (SQLite `CREATE INDEX`).
- Cache query results with `@st.cache_data` (Streamlit 1.19+) to avoid repeated expensive queries.
- Limit result sizes for charts (e.g., top 10) to keep UI responsive.
- Use `st.spinner()` around long-running queries.

## 9. Screenshot Checklist for Final Report
- [ ] KPI panel displaying total transactions, total volume, customer count, data quality %.
- [ ] Trend chart (daily/monthly transaction volume).
- [ ] Top customers visualization.
- [ ] Transaction type distribution chart.
- [ ] Data quality panel (quarantine counts or audit metrics).

## 10. Acceptance Criteria
- The Streamlit app starts successfully and connects to `warehouse/bank_warehouse.db`.
- KPIs display correct values derived from the warehouse.
- Filters update charts and KPIs interactively.
- Visualizations render without errors.
- Screenshots can be generated for the report.

## 11. Definition of Done
- `dashboard/app.py` exists and runs with `streamlit run dashboard/app.py`.
- The dashboard uses warehouse data and reflects changes after reloading.
- All required KPI cards, charts, and filters are present.
- Documentation describes how to run the dashboard and capture screenshots.
