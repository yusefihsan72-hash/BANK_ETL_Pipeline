# BANK ETL PIPELINE - Comprehensive Documentation

## Project Overview

**BANK ETL Pipeline** is a production-grade Extract, Transform, Load (ETL) system designed to automate the processing of banking customer and transaction data. The system reads CSV files from a monitored directory, applies comprehensive data transformation and validation rules, loads the processed data into a centralized SQLite data warehouse, and provides real-time analytics through an interactive Streamlit dashboard.

The project demonstrates modern data engineering practices including:
- Automated file processing and monitoring
- Multi-stage data validation and quality assurance
- Comprehensive audit trails and error handling
- Production-ready logging and monitoring
- Interactive analytics and visualization

---

## Project Information

| Property | Value |
|----------|-------|
| **Project Name** | BANK ETL Pipeline |
| **Type** | Data Integration System |
| **Purpose** | Automated banking data processing |
| **Status** | Production Ready |
| **GitHub** | https://github.com/yusefihsan72-hash/BANK_ETL_Pipeline |
| **Branch** | etl_bank_pipeline |
| **Last Updated** | April 3, 2026 |

---

## Architecture Overview

### System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    BANK ETL PIPELINE SYSTEM                     │
└─────────────────────────────────────────────────────────────────┘

INPUT LAYER (CSV Files)
├─ data/incoming/
│  ├─ XXXXXX_Customer.csv     (Customer data)
│  └─ XXXXXX_Transactions.csv (Transaction data)
│
PROCESSING PIPELINE (6 Stages)
├─ Stage 1: EXTRACTION
│  └─ File detection, validation, source identification
│
├─ Stage 2: TRANSFORMATION
│  └─ Standardization, normalization, derived fields
│
├─ Stage 3: VALIDATION
│  └─ Schema validation, business rules, quality checks
│
├─ Stage 4: LOADING
│  └─ Dimension & fact table population
│
├─ Stage 5: ARCHIVAL
│  └─ File organization, dated folder structure
│
└─ Stage 6: MONITORING
   └─ Dashboard updates, audit trails, alerts

OUTPUT LAYER
├─ data/archive/YYYY/MM/DD/ (Processed files)
├─ warehouse/bank_warehouse.db (Data warehouse)
├─ reports/ (Validation reports)
├─ quarantine/ (Failed records)
└─ logs/ (Processing logs)

ANALYTICS LAYER
└─ Streamlit Dashboard @ http://localhost:8501
   ├─ Customer Demographics
   ├─ Transaction Analysis
   ├─ Regional Distribution
   └─ Account Products
```

---

## Technology Stack

### Core Technologies

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| **Language** | Python | 3.13 | Main programming language |
| **Data Processing** | Pandas | 3.0.2 | Data manipulation & transformation |
| **Database** | SQLite3 | Built-in | Data warehouse backend |
| **ORM** | SQLAlchemy | 2.0.48 | Database abstraction layer |
| **Web Dashboard** | Streamlit | 1.56.0 | Interactive analytics dashboard |
| **Configuration** | PyYAML | 6.0.3 | Config file management |
| **File Monitoring** | Watchdog | 6.0.0 | Directory monitoring |
| **Testing** | Pytest | 9.0.2 | Unit testing framework |
| **Visualization** | Matplotlib/Seaborn | Latest | Data visualization |

### Development Tools

- **IDE**: VS Code
- **Version Control**: Git & GitHub
- **Command Line**: Windows PowerShell
- **Runtime**: Windows 10+

---

## Installation & Setup

### Prerequisites

- Python 3.13 or higher
- pip package manager
- 1GB free disk space
- Windows 10+ / Linux / macOS

### Step 1: Clone Repository

```bash
git clone https://github.com/yusefihsan72-hash/BANK_ETL_Pipeline.git
cd BANK_ETL_Pipeline
```

### Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

**Required Packages:**
```
pandas>=2.0
pyyaml>=6.0
streamlit>=1.22
pytest>=7.0
sqlalchemy>=2.0
python-dotenv>=1.0
watchdog>=3.0
matplotlib>=3.5
seaborn>=0.12
```

### Step 3: Verify Installation

```bash
python -c "import pandas; import streamlit; import sqlalchemy; print('✅ All dependencies installed')"
```

---

## Project Structure

```
BANK_ETL_Pipeline/
├── config/
│   ├── config.yaml              # Main pipeline configuration
│   ├── config_loader.py         # Configuration loading logic
│   └── logging_config.py        # Logging setup
│
├── data/
│   ├── incoming/                # Source CSV files (monitored)
│   ├── processed/
│   │   └── processed_files.json # Tracking processed files
│   └── archive/
│       └── 2026/04/03/          # Archived files (YYYY/MM/DD)
│
├── extraction/
│   ├── csv_extractor.py         # CSV file processing
│   ├── processed_tracker.py     # File processing history
│   └── schema.py                # Data schemas & patterns
│
├── transformation/
│   ├── standardization.py       # Data standardization
│   ├── cleaning.py              # Data cleaning & quality
│   └── enrichment.py            # Data enrichment & enrichment
│
├── validation/
│   ├── engine.py                # Validation rules engine
│   ├── rules.py                 # Business validation rules
│   └── report.py                # Report generation
│
├── warehouse/
│   ├── bank_warehouse.db        # SQLite database
│   ├── create_tables.sql        # Schema definition
│   └── loader.py                # Data loading logic
│
├── dashboard/
│   └── app.py                   # Streamlit dashboard
│
├── logs/
│   └── pipeline.log             # Processing logs
│
├── quarantine/
│   ├── customer_quarantine.csv  # Failed customer records
│   ├── transactions_quarantine.csv
│   └── pipeline_errors.csv
│
├── reports/
│   ├── dashboard_visualization.png
│   └── validation_*.json/md     # Validation reports
│
├── tests/
│   └── unit/
│       └── test_cleaning.py     # Unit tests
│
├── run.py                       # Main pipeline entry point
├── generate_sample_data.py      # Sample data generator
├── check_warehouse.py           # Warehouse data viewer
├── check_warehouse_stats.py     # Warehouse statistics
├── visualize_data.py            # Data visualization script
├── requirements.txt             # Dependencies
└── README.md                    # This file
```

---

## Configuration

### Main Configuration File: `config/config.yaml`

```yaml
version: 1
watcher:
  data_dir: "./data/incoming"            # Source directory
  processed_dir: "./data/processed"      # Tracking directory
  archive_dir: "./data/archive"          # Archive directory
  file_patterns:
    customer: '^\d{6}_Customer\.csv$'    # Customer file pattern
    transaction: '^\d{6}_Transactions\.csv$'
  polling_interval_seconds: 10

sources:
  csv:
    enabled: true
    encoding: "utf-8"
    delimiter: ","
  database:
    enabled: false
  api:
    enabled: false

logging:
  level: "INFO"
  file: "./logs/pipeline.log"
```

---

## Data Processing Pipeline

### 6-Stage Processing Flow

#### Stage 1: EXTRACTION
- Monitor `data/incoming/` directory every 10 seconds
- Detect new CSV files matching naming patterns
- Validate file integrity and completeness
- Identify data source (customer vs. transaction)
- Read CSV with proper encoding

**Input**: CSV files (XXXXXX_Customer.csv, XXXXXX_Transactions.csv)  
**Output**: Pandas DataFrame with raw data

#### Stage 2: TRANSFORMATION
- Standardize column names to pipeline schema
- Normalize categorical values (sex: M/F, region: uppercase)
- Convert data types (string → numeric, date parsing)
- Calculate derived fields (transaction amount from deposits/withdrawals)
- Generate transaction IDs from composite keys

**Customer Transformations**:
```python
- Rename: _id → customer_id
- Standardize: MALE/FEMALE → M/F
- Normalize: region names (add underscores)
- Convert: numeric fields with comma separation
- Map: YES/NO → True/False
```

**Transaction Transformations**:
```python
- Rename: Date → date, Description → description
- Parse: dates with format detection
- Calculate: amount = deposits - withdrawals
- Generate: transaction_id = customer_id + date + sequence
- Standardize: transaction_type from description
```

#### Stage 3: VALIDATION
- Schema validation (required columns present)
- Business rule validation (age 18-120, realistic amounts)
- Data quality checks (no NaN in keys, valid formats)
- Deduplication (remove duplicate records)
- Quarantine failed records

**Validation Rules**:
```
Customer:
  - customer_id required & unique
  - age: 18-120 range
  - valid regions: TOWN, INNER_CITY, RURAL, SUBURBAN

Transaction:
  - transaction_id required & unique
  - date: valid date format
  - amount: valid numeric value
```

**Output**: Two DataFrames
- `passed`: Valid records → warehouse
- `failed`: Invalid records → quarantine

#### Stage 4: LOADING
Load passed records into warehouse:
1. Load `dim_date` from transaction dates
2. Load `dim_transaction_type` from descriptions
3. Load `dim_account_profile` for account attributes
4. Load `dim_customer` with customer attributes
5. Load `fact_transactions` with transaction facts

#### Stage 5: ARCHIVAL
- Move successfully processed files to archive
- Create dated subdirectories (YYYY/MM/DD/)
- Track processed files in `processed_files.json`
- Handle duplicate filenames with timestamps

#### Stage 6: MONITORING
- Log all processing steps
- Record audit trail in `audit_load` table
- Generate validation reports (JSON & markdown)
- Send output to dashboard
- Alert on errors

---

## Database Schema

### Data Warehouse: SQLite

#### Dimension Tables

**dim_customer**
```sql
customer_sk (INT PRIMARY KEY)      # Surrogate key
customer_id (VARCHAR)               # Natural key
age (INT)
sex (VARCHAR)
region (VARCHAR)
income (DECIMAL)
married (BOOLEAN)
children (INT)
car (BOOLEAN)
save_act (BOOLEAN)
current_act (BOOLEAN)
mortgage (BOOLEAN)
pep (BOOLEAN)

Records: 1,150
```

**dim_date**
```sql
date_id (VARCHAR PRIMARY KEY)       # YYYYMMDD format
date (DATE)
year (INT)
quarter (INT)
month (INT)
day (INT)
day_of_week (INT)

Records: 92
```

**dim_transaction_type**
```sql
transaction_type_sk (INT PRIMARY KEY)
transaction_type (VARCHAR)
category (VARCHAR)
direction (VARCHAR)

Records: 2 (Interest, Transfer)
```

**dim_account_profile**
```sql
account_profile_sk (INT PRIMARY KEY)
customer_id (VARCHAR)
mortgage (BOOLEAN)
pep (BOOLEAN)
car (BOOLEAN)

Records: 1
```

#### Fact Table

**fact_transactions**
```sql
transaction_sk (INT PRIMARY KEY)    # Surrogate key
transaction_id (VARCHAR)            # Natural key
customer_sk (INT FOREIGN KEY)
date_sk (VARCHAR FOREIGN KEY)
transaction_type_sk (INT FOREIGN KEY)
account_profile_sk (INT FOREIGN KEY)
amount (DECIMAL)
balance (DECIMAL)
description (VARCHAR)

Records: 5,004
```

#### Audit Table

**audit_load**
```sql
load_id (INT PRIMARY KEY)
run_id (VARCHAR)
run_timestamp (TIMESTAMP)
source_table (VARCHAR)
source_count (INT)
target_table (VARCHAR)
target_count (INT)
duration_seconds (DECIMAL)
notes (VARCHAR)

Records: 13+
```

---

## Running the Pipeline

### Option 1: Run Pipeline (Monitoring Mode)

```bash
python run.py
```

**Output:**
```
2026-04-03 14:56:08,508 INFO pipeline - Pipeline starting...
2026-04-03 14:56:08,511 INFO pipeline - Pipeline watching : data\incoming
2026-04-03 14:56:08,511 INFO pipeline - Poll interval     : 10s | Ctrl+C to stop
```

The pipeline will:
- Monitor `data/incoming/` every 10 seconds
- Process new CSV files automatically
- Archive processed files
- Update warehouse
- Log all operations

**Stop with**: Press `Ctrl+C`

### Option 2: Generate Sample Data

```bash
python generate_sample_data.py
```

**Creates:**
- 500 customer records
- 10,000 transaction records
- Files: DDMMYY_Customer.csv, DDMMYY_Transactions.csv

### Option 3: View Warehouse Data

```bash
python check_warehouse.py
```

Complete warehouse data dump with all tables.

### Option 4: View Statistics

```bash
python check_warehouse_stats.py
```

**Output:**
```
Total Customers: 1,150
Total Transactions: 5,004
Average Transaction: $202.18
Customer Distribution by Region
Transaction Statistics
```

### Option 5: Generate Visualizations

```bash
python visualize_data.py
```

**Creates:** `reports/dashboard_visualization.png`

Contains 6 charts:
1. Customers by Region
2. Gender Distribution
3. Age Distribution
4. Income Distribution
5. Transaction Types
6. Account Products

### Option 6: Run Streamlit Dashboard

```bash
streamlit run dashboard/app.py
```

**Access:**
- Local: http://localhost:8501
- Network: http://192.168.1.110:8501

Real-time analytics with:
- Customer demographics
- Transaction analysis
- Regional distribution
- Account product metrics

---

## Current Project Status

### Dataset Statistics

| Metric | Value |
|--------|-------|
| **Total Customers** | 1,150 |
| **Total Transactions** | 5,004 |
| **Date Range** | 2020-2026 |
| **Average Transaction Amount** | $202.18 |
| **Total Transaction Volume** | $1,011,720.05 |
| **Transaction Range** | -$4,893.98 to $1,998.58 |

### Customer Distribution

| Region | Count | Percentage |
|--------|-------|-----------|
| INNER_CITY | 307 | 26.7% |
| RURAL | 298 | 25.9% |
| TOWN | 280 | 24.3% |
| SUBURBAN | 244 | 21.2% |
| **Total** | **1,150** | **100%** |

### Gender Distribution

| Gender | Count | Percentage |
|--------|-------|-----------|
| Male | 590 | 51.3% |
| Female | 560 | 48.7% |
| **Total** | **1,150** | **100%** |

### Account Products

| Product | Count | Percentage |
|---------|-------|-----------|
| PEP | 578 | 50.3% |
| Car | 548 | 47.7% |
| Mortgage | 372 | 32.3% |

### Transaction Types

| Type | Count | Percentage |
|------|-------|-----------|
| Interest | 2,536 | 50.7% |
| Transfer | 2,468 | 49.3% |

---

## CSV File Format

### Customer CSV Format

**Filename**: `DDMMYY_Customer.csv` (e.g., `040326_Customer.csv`)

**Columns**:
```
_id,age,sex,region,income,married,children,car,save_act,current_act,mortgage,pep
ID12102,40,MALE,TOWN,30085.10,YES,3,,NO,NO,YES,NO
ID12103,51,FEMALE,INNER_CITY,,NO,0,YES,,NO,,NO
```

**Field Descriptions**:
- `_id`: Customer identifier
- `age`: Age in years
- `sex`: MALE, FEMALE
- `region`: TOWN, INNER_CITY, RURAL, SUBURBAN
- `income`: Numeric income value (optional)
- `married`: YES/NO (optional)
- `children`: Number of children
- `car`: YES/NO (car account)
- `save_act`: YES/NO (savings account)
- `current_act`: YES/NO (current account)
- `mortgage`: YES/NO (mortgage product)
- `pep`: YES/NO (PEP product)

### Transaction CSV Format

**Filename**: `DDMMYY_Transactions.csv` (e.g., `040326_Transactions.csv`)

**Columns**:
```
customer_id,Date,Description,Deposits,Withdrawls,Balance
ID12203,20-Aug-2020,Interest,00.00,"4,893.98","39,151.80"
ID12536,20-Aug-2020,Debit Card,00.00,"5,593.11","33,558.69"
```

**Field Descriptions**:
- `customer_id`: Customer identifier
- `Date`: Transaction date (DD-Mon-YYYY format)
- `Description`: Interest, Debit Card, ATM Withdrawal, etc.
- `Deposits`: Deposit amount (currency format)
- `Withdrawls`: Withdrawal amount (currency format)
- `Balance`: Account balance after transaction

---

## Output Files & Reports

### Processed Files Archive

Location: `data/archive/YYYY/MM/DD/`

Example:
```
data/archive/2026/04/03/
├── 030426_Customer.csv
├── 030426_Transactions.csv
├── 040326_Customer.csv
└── 040326_Transactions.csv
```

### Validation Reports

Location: `reports/`

**Files Generated**:
- `validation_customer_TIMESTAMP.json` - Detailed validation metrics
- `validation_customer_TIMESTAMP.md` - Human-readable report
- `validation_transactions_TIMESTAMP.json`
- `validation_transactions_TIMESTAMP.md`

**Report Contents**:
```json
{
  "timestamp": "2026-04-03T11:15:08.756286",
  "source": "customer",
  "total_records": 1150,
  "passed": 1150,
  "failed": 0,
  "validation_rules": [...],
  "missing_values": {...},
  "data_quality_metrics": {...}
}
```

### Dashboard Visualization

File: `reports/dashboard_visualization.png`

6-panel visualization showing:
1. Customers by Region (bar chart)
2. Gender Distribution (bar chart)
3. Age Distribution (histogram)
4. Income Distribution (histogram)
5. Transaction Types (horizontal bar)
6. Account Products (bar chart)

### Quarantine Files

Location: `quarantine/`

**Files**:
- `customer_quarantine.csv` - Failed customer records
- `transactions_quarantine.csv` - Failed transaction records
- `pipeline_errors.csv` - Processing errors

---

## Features & Capabilities

### ✅ Core Features

1. **Automated CSV Processing**
   - Directory monitoring with 10-second polling
   - Automatic file detection by pattern
   - File stability verification

2. **Data Transformation**
   - 10+ standardization rules
   - Type conversion and normalization
   - Derived field calculation

3. **Comprehensive Validation**
   - Schema validation
   - Business rule enforcement
   - Data quality checks
   - Duplicate detection

4. **Data Warehouse**
   - Star schema design (4 dimensions + 1 fact)
   - Referential integrity
   - Historical tracking
   - Audit tables

5. **Error Handling**
   - Graceful error recovery
   - Detailed error logging
   - Quarantine system
   - Failed record tracking

6. **Monitoring & Analytics**
   - Real-time Streamlit dashboard
   - 6 visualization charts
   - Statistical analysis
   - Processing audit trail

7. **File Management**
   - Automatic file archival
   - Dated folder structure
   - Duplicate file handling
   - Processing history tracking

### 🔧 Advanced Features

- YAML-based configuration
- Comprehensive logging system
- JSON/Markdown report generation
- Multi-stage pipeline architecture
- Scalable design for 100K+ records
- Git version control integration

---

## Processing Example

### Input: Customer CSV
```
_id,age,sex,region,income,married,children,car,save_act,current_act,mortgage,pep
ID12102,40,MALE,TOWN,30085.10,YES,3,NO,NO,NO,YES,NO
```

### Processing Steps
1. **Extract**: Read CSV, validate format
2. **Transform**: 
   - _id → customer_id
   - MALE → M
   - YES → 1 (True)
   - NO → 0 (False)
3. **Validate**: Check age, income, required fields
4. **Load**: Insert into dim_customer table
5. **Archive**: Move file to data/archive/2026/04/03/
6. **Report**: Generate validation report

### Output: Warehouse Record
```
customer_sk=1
customer_id=ID12102
age=40
sex=M
region=TOWN
income=30085.10
married=1
children=3
car=0
save_act=0
current_act=0
mortgage=1
pep=0
```

---

## Testing & Quality Assurance

### Unit Tests

Location: `tests/unit/test_cleaning.py`

Run tests:
```bash
pytest tests/unit/ -v
```

### Data Validation

- 100% customer records validated
- 100% transaction records validated
- 0 records rejected or quarantined
- Complete audit trail maintained

### Performance

- Processes 1,150 customers in < 2 seconds
- Processes 5,004 transactions in < 3 seconds
- Minimal CPU and memory usage
- Scalable to 100K+ records

---

## File Processing Workflow

```
File Added to data/incoming/
        ↓
Pipeline Detects File (10s poll)
        ↓
Extract CSV Data
        ↓
Identify Source Type (Customer/Transaction)
        ↓
Transform Data (Standardize, Normalize)
        ↓
Clean Data (Remove duplicates, handle missing)
        ↓
Validate Data (Schema, Rules, Quality)
        ↓
├─→ PASSED → Load to Warehouse ✅
│           → Generate Report
│           → Archive File
│
└─→ FAILED → Move to Quarantine ❌
            → Log Error
            → Keep in data/incoming for retry
```

---

## Common Tasks

### Process New Data Files

1. Place CSV files in `data/incoming/`
2. Run: `python run.py`
3. Pipeline automatically processes files
4. Check reports in `reports/`
5. View data in dashboard

### Generate Sample Data

```bash
python generate_sample_data.py
python run.py
```

Creates 500 customers + 10,000 transactions.

### View Warehouse Contents

```bash
python check_warehouse.py              # Full dump
python check_warehouse_stats.py        # Statistics
streamlit run dashboard/app.py         # Interactive dashboard
```

### Create Visualizations

```bash
python visualize_data.py
```

Opens `reports/dashboard_visualization.png`

### Check Processing Status

```bash
git log --oneline                      # View commits
ls data/incoming/                      # Pending files
ls data/archive/2026/04/03/            # Processed files
cat logs/pipeline.log                  # Processing log
```

---

## Troubleshooting

### Issue: Dashboard won't open

**Solution**: Use localhost instead of network address
```bash
http://localhost:8501
```

### Issue: Files in incoming folder not being processed

**Solution**: 
1. Check pipeline is running: `python run.py`
2. Verify file naming: `DDMMYY_Customer.csv` / `DDMMYY_Transactions.csv`
3. Check logs: `cat logs/pipeline.log`

### Issue: Data validation failures

**Solution**:
1. Check `quarantine/pipeline_errors.csv` for error messages
2. Review `reports/validation_*.md` for details
3. Fix CSV format and retry

### Issue: Permission denied errors

**Solution**: Close any programs accessing the database:
```bash
taskkill /F /IM python.exe
```

---

## Project Metrics

### Code Statistics

- Total Python files: 20+
- Main pipeline: run.py (340+ lines)
- Total lines of code: 2,000+
- Test coverage: Core functions tested
- Documentation: Comprehensive

### Data Processing

- Total records processed: 6,154 (1,150 customers + 5,004 transactions)
- Success rate: 100%
- Processing time: < 5 seconds
- Storage used: 500 KB

### Validation

- Validation rules: 12+
- Data quality checks: 10+
- Error handling: Comprehensive

---

## Future Enhancements

1. **Database**: Migrate to PostgreSQL for enterprise scale
2. **API**: REST API for system integration
3. **Scheduling**: Cron jobs for automated processing
4. **Alerts**: Real-time email/Slack notifications
5. **ML**: Anomaly detection & fraud identification
6. **Containerization**: Docker for deployment
7. **Performance**: Database optimize indexing
8. **Security**: Data encryption & access controls

---

## Contact & Support

- **GitHub Repository**: https://github.com/yusefihsan72-hash/BANK_ETL_Pipeline
- **Branch**: etl_bank_pipeline
- **Status**: Active Development

---

## License & Usage

This project is created for educational and research purposes. All code is documented and available for learning and modification.

---

## Glossary

| Term | Definition |
|------|-----------|
| **ETL** | Extract, Transform, Load - data integration process |
| **Dimension** | Master data table (customer, date, product) |
| **Fact** | Transaction/event data table |
| **Surrogate Key** | Auto-generated primary key (SK) |
| **Natural Key** | Business identifier (customer_id) |
| **Quarantine** | Failed records storage area |
| **Schema** | Database structure definition |
| **Audit Trail** | Record of all system actions |
| **Pipeline** | Series of processing stages |
| **Warehouse** | Centralized data repository |

---

**Document Version**: 1.0  
**Last Updated**: April 3, 2026  
**Status**: Complete & Ready for Thesis Writing  

---

This comprehensive README provides all the information needed for an AI to understand and write a complete thesis on the BANK ETL Pipeline project. It covers architecture, implementation, results, and all technical details. 🚀
