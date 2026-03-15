# Phase Implementation Plan

This plan provides a phased implementation roadmap for the ETL + Data Warehouse + Dashboard project. Each phase includes objectives, tasks, outputs, dependencies, and risks.

---

## Phase 1: Foundation and Setup

### Objectives
- Establish a reproducible development environment.
- Define a clean, modular repository structure.
- Create base configuration and scaffolding.

### Tasks
- Initialize Git repository, add `.gitignore`, and create `README.md`.
- Create folder structure: `config/`, `extraction/`, `transformation/`, `validation/`, `loading/`, `warehouse/`, `dashboard/`, `data/`, `logs/`, `quarantine/`, `reports/`, `tests/`.
- Create `requirements.txt` and optionally `pyproject.toml`.
- Create base `config/config.yaml` with placeholders.
- Create initial `warehouse/create_tables.sql` with empty schema placeholders.
- Add sample data skeleton under `data/sample/`.
- Add basic logging setup (e.g., `logging_config.py`).

### Outputs
- Git repo with structured folders and baseline files.
- Working Python environment with dependencies installed.
- Base config file read by pipeline.

### Dependencies
- Python (3.10+ recommended).
- Access to workspace file system.

### Risks
- Missing initial requirements (e.g., exact dependency versions).
- Misaligned folder structure leading to import issues.

---

## Phase 2: Extraction

### Objectives
- Implement connectors for CSV, DB (config-only), and API (config-only).
- Enable reliable ingestion from watched directory with no reprocessing.

### Tasks
- Build `extraction/csv_extractor.py` with file watcher logic and processed-file tracking.
- Implement file name validation and encoding/delimiter checks.
- Create configuration-driven DB connector module `extraction/db_extractor.py` (no active connection required for demo).
- Create API connector module `extraction/api_extractor.py` (config-driven, stubbed response logic for demo).
- Log extraction metrics: record counts, runtime, file metadata.

### Outputs
- Working CSV extraction pipeline reading from `data/incoming/`.
- Processed file tracking store (JSON or SQLite table).
- Extraction logs with record counts.

### Dependencies
- `pandas` for CSV reading.
- `watchdog` or polling mechanism for directory watching.

### Risks
- File encoding/delimiter variety causing read failures.
- Race conditions when file is being written while watched.

---

## Phase 3: Transformation

### Objectives
- Normalize and clean extracted data to consistent schema.
- Implement deterministic transformation rules (type casting, normalization, enrichment).

### Tasks
- Implement transformation modules (e.g., `transformation/cleaning.py`, `transformation/enrichment.py`).
- Define transformation rule set and apply in a reproducible order.
- Add deduplication logic based on business keys.
- Unit test transformations with controlled inputs.

### Outputs
- Cleaned DataFrames for customers and transactions ready for validation.
- Transformation rule documentation.

### Dependencies
- Extraction outputs (DataFrames).

### Risks
- Ambiguity around field formats leading to inconsistent parsing.
- Over-normalization removing useful data.

---

## Phase 4: Validation

### Objectives
- Implement rule-based validation engine that quarantines invalid records.
- Produce data quality reports and track failure reasons.

### Tasks
- Build `validation/engine.py` and `validation/rules.py`.
- Implement schema validation, completeness checks, uniqueness checks, range checks, allowed value checks, and referential integrity stubs.
- Write quarantine outputs (`quarantine/customer_quarantine.csv`, `quarantine/transactions_quarantine.csv`).
- Generate validation summary report (pass/fail per rule, record counts).

### Outputs
- Validated data sets for loading (passing records).
- Quarantine datasets with failure reasons.
- Validation report artifacts.

### Dependencies
- Transformation outputs (cleaned DataFrames).

### Risks
- Rules too strict leading to excessive quarantine.
- Rules too lax failing to catch data quality issues.

---

## Phase 5: Warehouse and Loading

### Objectives
- Implement star schema in SQLite and load validated data into dimensional model.
- Provide auditing and record count reconciliation.

### Tasks
- Create `warehouse/create_tables.sql` with star schema (fact_transactions + dim_customer + dim_date + dim_transaction_type + dim_account_profile).
- Implement loader module `loading/loader.py` to upsert dimension tables and load fact table.
- Implement audit logging / table for run metadata.
- Add simple analytical queries to verify data consistency.

### Outputs
- Populated SQLite warehouse database file.
- Audit table with load statistics.

### Dependencies
- Validation pass datasets.
- SQLite engine (via SQLAlchemy or sqlite3).

### Risks
- Improper surrogate key management causing FK mismatches.
- Duplicate dimension rows leading to inflated counts.

---

## Phase 6: Dashboard

### Objectives
- Deliver a Streamlit dashboard showcasing KPIs, trends, and data quality.

### Tasks
- Build `dashboard/app.py` with Streamlit.
- Connect to the SQLite warehouse.
- Implement KPIs: total transactions, total volume, customer count, data quality %.
- Add charts: daily/monthly transaction trends, top customers, distribution of transaction types.
- Add filters (date range, region, transaction type).

### Outputs
- Running Streamlit app with interactive analytics.
- Screenshot assets for reports.

### Dependencies
- Loaded warehouse database.
- Streamlit installed.

### Risks
- Slow queries affecting dashboard responsiveness.
- Missing indices in warehouse leading to slow dashboards.

---

## Phase 7: Testing and DevOps

### Objectives
- Ensure code quality and reliability via automated tests and CI.
- Containerize the pipeline for reproducible execution.

### Tasks
- Write unit tests for extraction, transformation, validation, and loader modules.
- Write an integration test that runs the full pipeline on sample data.
- Create `Dockerfile` for pipeline execution.
- Optionally create `docker-compose.yml` (with SQLite, or placeholder PostgreSQL).
- Setup GitHub Actions workflow: install dependencies, run tests, optionally build Docker image.

### Outputs
- Test suite with coverage reports.
- CI pipeline configuration (`.github/workflows/ci.yml`).
- Docker image build configuration.

### Dependencies
- Test framework (pytest).
- Docker installed for local builds.

### Risks
- Tests brittle to data schema changes.
- CI pipeline slowness or configuration issues.

---

## Phase 8: Evaluation and Reporting

### Objectives
- Produce a comprehensive evaluation report demonstrating metrics, quality, and runtime.

### Tasks
- Capture record counts at each stage (Extract/Transform/Validate/Load).
- Compute data quality metrics (completeness %, duplicates %, invalid %).
- Collect runtime metrics (per stage duration).
- Save screenshots from the dashboard.
- Assemble a final evaluation report (`reports/evaluation.md`).

### Outputs
- Evaluation report with tables, charts, and screenshots.
- Supporting artifacts (logs, metrics, report data files).

### Dependencies
- Pipeline execution metadata from previous phases.

### Risks
- Missing instrumentation to capture metrics.
- Incomplete documentation reducing evaluation clarity.

---

# 15. Delivery Roadmap

| Milestone | Deliverables | Success Criteria |
|---|---|---|
| Foundation & Setup | Repo structure, config file, sample data, requirements | Repo builds, config loads, folder structure matches plan |
| Extraction | CSV extractor, file watcher, processed tracking | Can ingest sample CSVs once and log counts |
| Transformation | Cleaning/enrichment modules, dedupe logic | Cleaned outputs match expected schema; tests pass |
| Validation | Rule engine, quarantine output, report | Invalid records quarantined, validation summary generated |
| Warehouse Loading | SQLite schema and loader, audit log | Data loaded with correct record counts and FK integrity |
| Dashboard | Streamlit app with KPIs | Dashboard renders and updates with warehouse data |
| Testing & DevOps | Unit/integration tests, CI workflow, Dockerfile | CI pipeline passes; Docker image builds successfully |
| Evaluation & Reporting | Evaluation report, metrics + screenshots | Report includes all required tables/metrics and is submission-ready |

---

# 16. Evaluation Framework

Measure project success using the following metrics and include them in final reporting.

## Metrics

### Record Counts by Stage
- **Extracted**: number of rows read from each source.
- **Transformed**: rows after cleaning/deduplication.
- **Validated**: rows passing validation (loaded) and rows quarantined.
- **Loaded**: rows inserted into warehouse (fact + dimensions).

### Data Quality Metrics
- **Completeness %** = (non-null critical fields / total) × 100.
- **Duplicate %** = (duplicates detected / total) × 100.
- **Invalid Value %** = (records with invalid values / total) × 100.
- **Quarantine Volume** = number of rows quarantined by source.

### Runtime Metrics
- Duration per stage: extraction, transformation, validation, loading.
- End-to-end pipeline runtime.

### Warehouse Load Counts
- Fact table row count.
- Dimension table row counts.
- Referential integrity checks (FK counts vs expected).

## Recommended Report Tables/Charts

### Tables
- Stage counts: Extract/Transform/Validate/Load.
- Validation summary: rule name, pass count, fail count.
- Quarantine summary: source, failure reasons, record count.
- Warehouse table counts with load timestamps.

### Charts
- Daily transaction volume trend (line chart).
- Completeness % over time (trend line).
- Top N customers by transaction volume (bar chart).
- Distribution of transaction types (pie chart).

---

# 17. Recommendations and Critical Notes

## Design Improvements
- Introduce a lightweight orchestration layer (Airflow/Prefect) if scaling beyond sample data.
- Add configuration-driven rule sets so business users can adjust validation without code changes.
- Consider a metadata store (SQLite or JSON) for lineage and audit tracking.

## Likely Implementation Pitfalls
- **File race conditions:** Ensure file watching waits until file writes complete (e.g., temporary extension, checksum stabilization).
- **Schema drift:** Source schema changes can break validation; add schema versioning and backward compatibility handling.
- **Duplicate handling:** Choosing keep-first vs keep-last can affect analytics; document and test chosen strategy.

## Academic / Reporting Tips
- Keep the report focused on measurable outcomes (metrics + screenshots).
- Clearly state assumptions and limitations (what is implemented vs configured-only). 
- Include a “Lessons Learned” or “Next Steps” section.

## Submission-Readiness Checklist
- [ ] Repository has README with setup/run instructions.
- [ ] `config/config.yaml` is populated with realistic values.
- [ ] Sample data exists under `data/sample/` and is used by tests.
- [ ] Pipeline runs end-to-end and populates `warehouse/bank_warehouse.db`.
- [ ] Validation output and quarantine files exist.
- [ ] Dashboard runs and connects to warehouse.
- [ ] CI pipeline runs and passes.
- [ ] Evaluation report includes metric tables, charts, and screenshots.
