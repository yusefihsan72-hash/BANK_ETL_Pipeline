# Phase 4: Validation

## 1. Purpose
This phase implements a data quality and validation engine that checks transformed datasets, quarantines invalid records with explicit failure reasons, and generates measurable validation reports for evaluation and auditing.

## 2. Objectives
- Implement a rule-based validation engine.
- Quarantine invalid records with detailed failure reasons.
- Generate validation reports that support evaluation metrics.

## 3. Scope
- Input: Cleaned DataFrames from the transformation phase (customers and transactions).
- Output: Validated DataFrames for loading, quarantine files for invalid records, and reports summarizing validation results.

## 4. Inputs Required
- Transformed DataFrames for customer and transaction sources.
- Configuration for validation rules (schema definitions, allowed values, thresholds).
- Access to warehouse data for referential integrity checks (optional at this stage).

## 5. Detailed Step-by-Step Implementation

### 5.1 Create Validation Module Structure
1. Ensure the following files exist:
   - `validation/__init__.py`
   - `validation/engine.py`
   - `validation/rules.py`
   - `validation/report.py`
   - `validation/utils.py` (optional helpers)

### 5.2 Define Validation Rule Types and Schema
1. Define a validation schema configuration (e.g., in `config/config.yaml` or a dedicated YAML file).
2. Example schema definition within `config/config.yaml`:
```yaml
validation:
  schema:
    customer:
      columns:
        - name: customer_id
          dtype: string
          required: true
        - name: age
          dtype: integer
          required: true
        - name: sex
          dtype: string
          required: true
        - name: region
          dtype: string
          required: true
    transaction:
      columns:
        - name: transaction_id
          dtype: string
          required: true
        - name: customer_id
          dtype: string
          required: true
        - name: date
          dtype: date
          required: true
        - name: amount
          dtype: float
          required: true
      allowed_values:
        transaction_type: ["ATM", "Transfer", "Bill", "Interest", "Deposit", "Withdrawal"]
```
3. In `validation/rules.py`, define rule classes/functions for each check type.

### 5.3 Build `validation/rules.py`
1. Define a `ValidationResult` data structure (e.g., dataclass) to capture:
   - `row_index` or unique identifier
   - `failure_reasons` (list of strings)
   - `rule_name`
   - `details` (optional extra info)
2. Implement rule functions:
   - `validate_schema(df, schema)`
   - `validate_completeness(df, required_columns)`
   - `validate_uniqueness(df, key_columns)`
   - `validate_range(df, column, min_value=None, max_value=None)`
   - `validate_allowed_values(df, column, allowed_values)`
   - `validate_referential_integrity(df, fk_column, reference_df, reference_key)`
3. Each rule should return a list of failure records (row index + reason), or a boolean mask.

### 5.4 Build `validation/engine.py`
1. Create a `ValidationEngine` class handling:
   - Loading schema definitions from config.
   - Running all rules in a defined order.
   - Aggregating failure reasons per row.
   - Producing:
     - `passed_df` (valid rows)
     - `failed_df` (invalid rows with failure details)
2. Implement workflow:
   1. Apply schema validation (columns exist, types match/castable).
   2. Apply completeness checks (required fields not null).
   3. Apply uniqueness checks (business keys).
   4. Apply consistency/range checks (e.g., `age` between bounds, `amount` non-null).
   5. Apply allowed value checks (enums, categories).
   6. Apply referential integrity (customer_id exists in customer set for transactions).
3. Maintain a `failure_reasons` column (list or semicolon-joined string) for each invalid row.

### 5.5 Record-Level Failure Handling
1. Design a record structure for failures:
   - `failure_reasons` column containing a list of failure messages.
   - `validation_stage` column (optional) indicating which stage failed.
2. When a row fails multiple rules, append reasons:
   - `"missing_required_field:customer_id"`
   - `"invalid_value:age=-1"`
3. Ensure failure reasons are human-readable and consistent for reporting.

### 5.6 Quarantine Output Generation
1. Create `quarantine/customer_quarantine.csv` and `quarantine/transactions_quarantine.csv`.
2. Each quarantine file should include:
   - All original fields from input.
   - `failure_reasons` (string or JSON array).
   - `validation_run_id` (UUID or timestamp).
   - `source_file` (if available).
3. Append new failures to existing quarantine file (avoid overwriting). Use a timestamped archive if needed.

### 5.7 Validation Summary Reports (`validation/report.py`)
1. Generate summary report data structures:
   - `rules_executed` with pass/fail counts.
   - `record_counts` (total, passed, failed).
   - `failure_distribution` (most common failure reasons).
2. Write summaries to:
   - `reports/validation_summary_{timestamp}.json` (structured data)
   - `reports/validation_summary_{timestamp}.md` (human-readable)
3. Example report structure (Markdown):
   - Total records processed
   - Records passed / failed
   - Top 10 failure reasons
   - Rule-specific pass/fail counts

### 5.8 Balancing Strictness vs Practicality
1. Define rule severity levels: `ERROR` (quarantine) vs `WARN` (log but pass).
2. Use config to toggle severity (e.g., allow missing non-critical fields but log warnings).
3. Document decisions in report.

### 5.9 Suggested Tests for Validation Rules
1. Create unit tests under `tests/unit/`:
   - `test_schema_validation.py`
   - `test_completeness_validation.py`
   - `test_uniqueness_validation.py`
   - `test_range_validation.py`
   - `test_allowed_values_validation.py`
   - `test_referential_integrity.py`
2. Each test should:
   - Construct a small DataFrame with known good/bad rows.
   - Run the validation engine on the DataFrame.
   - Assert the number of passed/failed records and specific failure reasons.
3. Example assertion:
```python
assert "missing_required_field:customer_id" in failed_df.loc[0, "failure_reasons"]
```

## 6. Suggested Report Structure for Validation Outputs
- Header with run metadata (timestamp, pipeline run id).
- Summary statistics (records processed, passed, failed).
- Table: rule name, description, pass count, fail count.
- Table: top 10 failure reasons with counts.
- Notes on any relaxed rules or tolerated issues.

## 7. Acceptance Criteria
- Validation engine runs and splits data into `passed_df` and `failed_df`.
- Failed records are written to quarantine CSVs with detailed failure reasons.
- Validation reports are generated and saved under `reports/`.
- Validation rules are test-covered and pass.

## 8. Definition of Done
- `validation/engine.py`, `validation/rules.py`, and `validation/report.py` exist and are functional.
- Quarantine files exist with expected columns and accurate failure reasons.
- Validation reports are generated and contain required metrics.
- Unit tests pass and cover key validation rules.
- The pipeline can be run end-to-end with validation stage producing expected outputs.
