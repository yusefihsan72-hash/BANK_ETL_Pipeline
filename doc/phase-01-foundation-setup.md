# Phase 1: Foundation and Setup

## 1. Purpose
This phase establishes a reproducible development environment and a clean modular repository structure for the ETL + Data Warehouse + Dashboard project.

## 2. Objectives
- Establish a reproducible development environment.
- Define a clean, modular repository structure.
- Create base configuration and scaffolding to support later pipeline phases.

## 3. Scope
This phase covers everything required to get a developer from a blank workspace to a runnable project skeleton, including:
- Git initialization and basic repo hygiene
- Project folder structure and placeholder files
- Base configuration for the pipeline
- Sample data stubs and logging setup
- Explicit notes for future phases (bootstrapping guidelines)

## 4. Inputs Required
- A working Python installation (3.10+ recommended)
- Access to the workspace filesystem
- Basic familiarity with Git

## 5. Detailed Step-by-Step Implementation

### Step 1: Initialize the Git Repository
1. Open a terminal in `d:\BANK_ETL_Pipeline`.
2. Run:
   ```powershell
   git init
   git config user.name "Your Name"
   git config user.email "you@example.com"
   ```
3. Create an initial commit after adding the first files.

### Step 2: Add `.gitignore`
1. Create `.gitignore` at the repository root.
2. Use a standard Python `.gitignore` template, then add project-specific entries.

Suggested `.gitignore` content:
```gitignore
# Python
__pycache__/
*.py[cod]
*.pyo
*~

# Virtual environments
.venv/
venv/
env/

# Packages
*.egg-info/
*.egg

# SQLite
*.db

# Logs
logs/

# IDEs
.vscode/
.idea/

# OS
.DS_Store
Thumbs.db
```

### Step 3: Create `README.md`
1. Create `README.md` at repo root.
2. Include sections:
   - Project overview
   - How to set up the environment
   - How to run the pipeline
   - Folder structure description
   - How to run tests
   - How to run the dashboard

Suggested `README.md` structure:
```markdown
# BANK_ETL_Pipeline

## Overview
A modular ETL pipeline for bank data with data quality validation, a SQLite star-schema warehouse, and a Streamlit dashboard.

## Setup
1. Create a Python virtual environment.
2. Install dependencies: `pip install -r requirements.txt`.

## Run
- `python -m pipeline.run` (TBD)

## Testing
- `pytest`

## Dashboard
- `streamlit run dashboard/app.py`
```

### Step 4: Create Folder Structure
1. Create the following directories at the repository root:
   - `config/`
   - `extraction/`
   - `transformation/`
   - `validation/`
   - `loading/`
   - `warehouse/`
   - `dashboard/`
   - `data/`
   - `logs/`
   - `quarantine/`
   - `reports/`
   - `tests/`
2. Inside `data/`, create subfolders:
   - `incoming/` (for raw input files)
   - `processed/` (for files moved after successful processing)
   - `sample/` (for bundled sample data for tests/demos)

### Step 5: Create `requirements.txt` and optional `pyproject.toml`
1. Create `requirements.txt` with core dependencies:
   - pandas
   - pyyaml
   - streamlit
   - pytest
   - sqlalchemy
   - python-dotenv (optional)
   - watchdog (optional)

Example `requirements.txt`:
```
pandas>=2.0
pyyaml>=6.0
streamlit>=1.22
pytest>=7.0
sqlalchemy>=2.0
python-dotenv>=1.0
watchdog>=3.0
```

2. Optionally create `pyproject.toml` with project metadata and build system (PEP 621). This is not required for phase 1, but can be added for modern tooling.

### Step 6: Create base `config/config.yaml`
1. Create `config/config.yaml` with initial configuration values.
2. Use the structure defined in the design document.

Example `config/config.yaml`:
```yaml
version: 1
watcher:
  data_dir: "./data/incoming"
  processed_dir: "./data/processed"
  file_patterns:
    customer: "^\\d{6}_Customer\\.csv$"
    transaction: "^\\d{6}_Transactions\\.csv$"
  polling_interval_seconds: 10

sources:
  csv:
    enabled: true
    encoding: "utf-8"
    delimiter: ","
    quotechar: '"'

  database:
    enabled: false

  api:
    enabled: false

logging:
  level: "INFO"
  file: "./logs/pipeline.log"
```

### Step 7: Create initial `warehouse/create_tables.sql` placeholder
1. Create file `warehouse/create_tables.sql`.
2. Add placeholder SQL comments describing the intended schema.

Example content:
```sql
-- Star schema for banking analytics
-- Table: dim_customer
-- Table: dim_date
-- Table: dim_transaction_type
-- Table: dim_account_profile
-- Table: fact_transactions

-- Add real DDL in Phase 5.
```

### Step 8: Add sample data skeleton under `data/sample/`
1. Create `data/sample/` directory if not already present.
2. Create placeholder CSV files:
   - `data/sample/240101_Customer.csv`
   - `data/sample/240101_Transactions.csv`
3. Add header rows with example columns. No need for real data yet.

Example `240101_Customer.csv`:
```csv
customer_id,age,sex,region,income,married,children,car,save_act,current_act,mortgage,pep
```

Example `240101_Transactions.csv`:
```csv
transaction_id,customer_id,date,transaction_type,amount,balance,description
```

### Step 9: Add logging setup (`logging_config.py`)
1. Create `logging_config.py` at repo root (or in `config/`).
2. Provide a reusable function to initialize logging based on `config/config.yaml`.

Example:
```python
import logging
from pathlib import Path


def init_logging(log_file: str, level: str = "INFO"):
    Path(log_file).parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ],
    )
```

### Step 10: Define coding conventions and bootstrapping notes
1. Create a `CONTRIBUTING.md` or add a section in `README.md`.
2. Include conventions such as:
   - Python style (PEP8)
   - Type hinting and docstrings
   - Module naming conventions (snake_case)
   - Logging usage
   - How to run the pipeline and tests

Example note fragment:
> Use `python -m venv .venv` to create a virtual environment. Activate it with `.
> .venv\Scripts\activate` (Windows) or `source .venv/bin/activate` (Unix).

## 6. Suggested File/Module Changes
After Phase 1, the following files should exist:
- `.gitignore`
- `README.md`
- `requirements.txt`
- (optional) `pyproject.toml`
- `config/config.yaml`
- `warehouse/create_tables.sql`
- `logging_config.py`
- Sample data placeholders under `data/sample/`

## 7. Outputs / Deliverables
- Initialized Git repository with initial commit
- Repository folder structure meeting project design
- Base configuration file
- Placeholder SQL schema file
- Sample data skeleton
- Logging initialization helper
- `README.md` with setup notes and structure overview

## 8. Dependencies
- Python 3.10+
- Git
- Basic shell / PowerShell access

## 9. Risks and Mitigations
- **Risk:** Missing or inconsistent folder structure can cause import errors.  
  **Mitigation:** Verify folder existence and add `__init__.py` where needed.

- **Risk:** Dependence on global Python packages.  
  **Mitigation:** Use virtual environments and `requirements.txt`.

- **Risk:** `.gitignore` missing entries can commit sensitive files.  
  **Mitigation:** Add `.db`, `.env`, and `logs/` to `.gitignore` early.

## 10. Validation Checklist
- [ ] Git repo initialized and has first commit.
- [ ] `.gitignore` exists and contains standard Python ignores.
- [ ] `README.md` provides basic setup/run instructions.
- [ ] Folder structure exists as specified.
- [ ] `requirements.txt` lists core dependencies.
- [ ] `config/config.yaml` exists with base settings.
- [ ] `warehouse/create_tables.sql` placeholder exists.
- [ ] Sample CSV files exist with header rows.
- [ ] `logging_config.py` exists and can be imported.

## 11. Acceptance Criteria
- A new developer can clone the repo, create a virtual environment, install dependencies, and locate the core project structure without additional guidance.
- The repository contains placeholders for all major modules required by later phases.
- The project is ready for Phase 2 development (Extraction) with minimal setup.

## 12. Definition of Done
- All required files and folders exist and are version controlled.
- Basic configuration is in place and loads without syntax errors.
- Sample data skeleton is present.
- The repository leverages a consistent Python environment (via `requirements.txt`).
- The developer handbook (`README.md`) describes how to bootstrap and where to start development.
