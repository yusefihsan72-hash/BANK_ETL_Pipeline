# Phase 3: Transformation

## 1. Purpose
This phase standardizes, cleans, normalizes, and enriches extracted customer and transaction data so it becomes consistent and ready for validation and warehouse loading.

## 2. Objectives
- Normalize and clean extracted data to a consistent schema.
- Implement deterministic transformation rules (type casting, normalization, enrichment).
- Ensure transformation output is reproducible and deterministic.
- Provide unit tests that validate transformation logic.

## 3. Scope
- Input: DataFrames produced by the extraction layer for customer and transaction sources.
- Output: Cleaned DataFrames conforming to expected schemas, ready for validation.
- Includes: type standardization, missing value handling, deduplication, category normalization, and derived field creation.

## 4. Inputs Required
- Extracted `pandas.DataFrame` objects for customers and transactions.
- Access to `config/config.yaml` for transformation rules and thresholds.
- Business key definitions (e.g., `customer_id`, `transaction_id`).

## 5. Detailed Step-by-Step Implementation

### 5.1 Create Transformation Module Structure
1. Ensure the following files exist:
   - `transformation/__init__.py`
   - `transformation/cleaning.py`
   - `transformation/standardization.py`
   - `transformation/enrichment.py`
   - `transformation/utils.py` (optional helper functions)

### 5.2 Define Expected Transformation Input/Output
1. Define `TransformationResult` typed structure:
```python
from dataclasses import dataclass
import pandas as pd

@dataclass
class TransformationResult:
    source: str
    df: pd.DataFrame
    metadata: dict
```
2. Document expected input columns (from extraction) and expected output columns (post-transformation) for each source.

#### Customer Input/Output
- Input columns (must include):
  - `customer_id`, `age`, `sex`, `region`, `income`, `married`, `children`, `car`, `save_act`, `current_act`, `mortgage`, `pep`
- Output columns (examples):
  - Same columns, plus normalized fields such as `sex_norm`, `region_norm`, and flags `income_missing`, `age_missing`.

#### Transaction Input/Output
- Input columns (must include):
  - `transaction_id`, `customer_id`, `date`, `transaction_type`, `amount`, `balance`, `description`
- Output columns (examples):
  - Same columns, plus derived fields such as `transaction_date`, `transaction_year`, `transaction_month`, `amount_clean`, `amount_negative`.

### 5.3 Define Transformation Rule Execution Order
A deterministic order ensures reproducibility. Suggested pipeline:
1. **Schema enforcement**: Ensure required columns exist and cast to expected types (as much as possible).
2. **Standardization**: Normalize strings, fix casing, trim whitespace, map category values.
3. **Missing value handling**:
   - Drop rows missing critical keys.
   - Impute or flag non-critical nulls.
4. **Deduplication**: Remove duplicates based on business keys.
5. **Enrichment**: Compute derived fields (date parts, flags, aggregated values).
6. **Final validation prep**: Ensure output columns exist and types are correct.

### 5.4 Implement Standardization (`transformation/standardization.py`)

#### 5.4.1 Responsibilities
- Coerce column types (int, float, date, bool).
- Normalize categorical values (sex, region, transaction type).
- Normalize numeric formats (strip currency symbols, remove commas).

#### 5.4.2 Suggested Functions
- `coerce_to_int(series, default=None)`
- `coerce_to_float(series, default=None)`
- `coerce_to_bool(series, true_values, false_values, default=None)`
- `coerce_to_date(series, formats, default=None)`
- `normalize_category(series, mapping, default)`

#### 5.4.3 Business Rule Examples
- `sex` should map to `{'M': 'M', 'F': 'F', 'Male': 'M', 'Female': 'F'}`.
- `region` values should be uppercased and trimmed (e.g., `north-east` -> `NORTH_EAST`).
- `transaction_type` should map to base categories (e.g., `ATM Withdrawal` -> `Withdrawal`).

### 5.5 Implement Cleaning (`transformation/cleaning.py`)

#### 5.5.1 Responsibilities
- Drop rows missing required business keys.
- Handle missing values based on criticality.
- Detect and handle non-conformant values (e.g., negative ages).

#### 5.5.2 Missing Value Policies
- **Critical fields (drop)**: `customer_id`, `transaction_id`, `date`, `amount`.
- **Non-critical fields (flag)**: `income`, `description`, `balance`.

#### 5.5.3 Suggested Functions
- `drop_missing_keys(df, key_columns)`
- `flag_missing(df, columns, flag_suffix="_missing")`
- `impute_missing(df, column, strategy="median"|"mean"|"constant", value=None)`

#### 5.5.4 Business Rule Examples
- If `age` is missing or outside [18, 120], set `age_missing=True` and `age` to `None`.
- If `amount` is missing or non-numeric, drop the transaction row.

### 5.6 Implement Deduplication (`transformation/cleaning.py` or `transformation/utils.py`)

#### 5.6.1 Business Keys
- Customer dedupe key: `customer_id`.
- Transaction dedupe key: `transaction_id`.

#### 5.6.2 Deduplication Strategy
- Keep the first occurrence by default (configurable).
- Optionally keep the latest based on `date`.

#### 5.6.3 Suggested Function
- `deduplicate(df, subset, keep="first")`

### 5.7 Implement Enrichment (`transformation/enrichment.py`)

#### 5.7.1 Responsibilities
- Derive fields that aid analytics and validation.
- Compute date parts and flags.

#### 5.7.2 Example Derived Fields
- `transaction_date` (datetime)
- `transaction_year`, `transaction_month`, `transaction_day_of_week`
- `amount_abs` (absolute transaction amount)
- `is_debit` (amount < 0) / `is_credit` (amount >= 0)

#### 5.7.3 Suggested Functions
- `derive_date_parts(df, date_column, tz=None)`
- `derive_amount_flags(df, amount_column, output_prefix="amount")`

### 5.8 Make Transformation Deterministic and Reproducible
- Avoid random operations (no shuffle, no sampling).
- Use fixed sort order when dropping duplicates (e.g., sort by `transaction_id` then `date`).
- Fix transformation logic via config or code constants (no time-based defaults).

### 5.9 Add Unit Tests for Transformations
1. Create test files under `tests/unit/`:
   - `tests/unit/test_cleaning.py`
   - `tests/unit/test_standardization.py`
   - `tests/unit/test_enrichment.py`
2. Each test should:
   - Build a small DataFrame fixture.
   - Apply transformation functions.
   - Assert expected output schema and values.

Example test case:
```python
import pandas as pd
from transformation.cleaning import drop_missing_keys


def test_drop_missing_customer_id():
    df = pd.DataFrame({"customer_id": ["c1", None], "age": [30, 25]})
    result = drop_missing_keys(df, ["customer_id"])
    assert len(result) == 1
    assert result.iloc[0]["customer_id"] == "c1"
```

## 6. Suggested Execution Order for Transformation Rules
1. **Schema enforcement** (cast types, ensure required columns present)
2. **Standardization** (normalize strings, map categories)
3. **Missing value handling** (drop critical, flag non-critical)
4. **Deduplication** (remove duplicates by keys)
5. **Enrichment** (derive new fields and date parts)
6. **Final schema projection** (select required output columns)

## 7. Business-Rule-Focused Explanation

### Data Type Standardization
- **Why:** Ensure all numeric columns are numeric, date columns are datetime, boolean values are consistent.
- **Example:** Convert `"1,234"` to `1234.0` for `income`.

### Missing Value Handling
- **Why:** Prevent downstream errors and make data quality visible.
- **Example:** Drop transactions missing `transaction_id` (critical key). Flag missing `balance` for review.

### Deduplication
- **Why:** Prevent inflated metrics and ensure consistent analytics.
- **Example:** If `transaction_id` repeats, keep earliest record (or latest if configured).

### Category Normalization
- **Why:** Standardized categories ensure reliable grouping and joins.
- **Example:** Normalize `region` values to a fixed set and map variants (e.g., `North-East` -> `NE`).

### Enrichment
- **Why:** Derived fields simplify analytics and enable richer KPIs.
- **Example:** Extract `transaction_month` for time-series reporting.

## 8. Input/Output Expectations

### Customer Dataset
- **Input:** Raw extracted customer DataFrame.
- **Output:** Cleaned customer DataFrame with normalized categorical fields and missing flags.

### Transaction Dataset
- **Input:** Raw extracted transaction DataFrame.
- **Output:** Cleaned transaction DataFrame with date-derived fields, normalized types, and deduplicated records.

## 9. Guidance for Documenting Transformation Rules in the Report
- Create a table of transformation rules with columns:
  - Rule name
  - Target field(s)
  - Description
  - Business rationale
  - Example before/after
- Include a short narrative for each transformation category (standardization, missing values, dedupe, enrichment).

## 10. Acceptance Criteria
- Transformation modules exist and are importable.
- Customer and transaction DataFrames are cleaned and conform to expected output schema.
- Rules are executed in a deterministic order producing consistent results on repeated runs.
- Unit tests cover key transformation logic and pass.

## 11. Definition of Done
- Transformation code is committed and passes unit tests.
- Cleaned DataFrames are ready for validation (no missing critical keys, normalized categories, deduplicated).
- Transformation rules are documented in the report (table + examples).
- A developer can rerun the transformation and get identical output given identical input.
