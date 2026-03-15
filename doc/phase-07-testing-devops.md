# Phase 7: Testing and DevOps

## 1. Purpose
This phase ensures reliability, repeatability, and engineering quality through automated tests, containerization, and continuous integration using GitHub Actions.

## 2. Objectives
- Add automated unit and integration tests across extraction, transformation, validation, and loading.
- Containerize the pipeline for reproducible execution.
- Create a CI workflow to run tests and detect regressions on every change.

## 3. Scope
- Unit tests for each module (extraction, transformation, validation, loading).
- Integration test that executes the pipeline end-to-end using sample data.
- Dockerfile (and optional docker-compose) for running the pipeline.
- GitHub Actions workflow for automated testing and optional Docker build.

## 4. Inputs Required
- Pipeline codebase with modules for extraction, transformation, validation, and loading.
- Sample data under `data/sample/`.
- `requirements.txt` with dependencies.
- A `tests/` directory structure.

## 5. Detailed Step-by-Step Implementation

### 5.1 Testing Strategy Overview
- **Unit tests** validate individual functions and classes in isolation.
- **Integration test** validates the full pipeline end-to-end on a known dataset.
- **Test data** should be deterministic and small.
- Use `pytest` as the test runner.

### 5.2 Test Folder Structure and Naming Conventions
1. Create the following structure under `tests/`:
   - `tests/unit/`
   - `tests/integration/`
   - `tests/fixtures/`
2. Naming conventions:
   - Unit test files: `test_<module>.py` (e.g., `test_csv_extractor.py`).
   - Integration tests: `test_integration_pipeline.py`.
   - Test functions: `test_<behavior>_...`.

### 5.3 Unit Tests
#### 5.3.1 Extraction Tests
- Validate that CSV files are correctly parsed into DataFrames.
- Verify file pattern validation rejects invalid file names.
- Confirm processed-file tracking works (e.g., marks files as processed and skips).

Example tests:
- `test_csv_extractor_reads_customer_file`.
- `test_processed_tracker_skips_already_processed_file`.

#### 5.3.2 Transformation Tests
- Test standardization conversions (e.g., string -> numeric, boolean normalization).
- Test missing value flagging and dropping of critical rows.
- Test deduplication by business keys.

Example tests:
- `test_standardize_sex_values`.
- `test_deduplicate_transactions_by_transaction_id`.

#### 5.3.3 Validation Tests
- Test schema validation identifies missing columns.
- Test completeness checks identify nulls in required fields.
- Test uniqueness checks on business keys.
- Test referential integrity (e.g., transaction customer_id must exist).

Example tests:
- `test_validate_missing_required_field`.
- `test_validate_unique_transaction_id`.

#### 5.3.4 Loading Tests
- Test that dimension upserts create unique surrogate keys.
- Test that fact rows reference valid surrogate keys.
- Test audit row creation.

Example tests:
- `test_load_dim_customer_inserts_new_customer`.
- `test_load_fact_transaction_references_dimension_keys`.

### 5.4 Integration Test
1. Create `tests/integration/test_pipeline_end_to_end.py`.
2. Setup should:
   - Copy sample data into a temporary input directory.
   - Run the pipeline entry point (`run_pipeline()` or equivalent).
   - Assert that warehouse database exists and contains expected row counts.
   - Assert quarantine files are created (if expected).
3. Use temporary directories (`tmp_path` fixture) to avoid polluting the repo.

Example integration assertion:
```python
assert execute_sql("SELECT COUNT(*) FROM fact_transactions") == expected_count
```

### 5.5 Test Fixtures and Reuse
- Use `tests/fixtures/` for reusable DataFrames or sample CSVs.
- Use `pytest` fixtures to create temporary warehouse DB and config.

Example fixture:
```python
@pytest.fixture
def sample_customer_df():
    return pd.DataFrame({"customer_id": ["c1"], "age": [30], ...})
```

### 5.6 Dockerfile
1. Create `Dockerfile` at repo root.
2. Use a lightweight base image (e.g., `python:3.11-slim`).
3. Install dependencies from `requirements.txt`.
4. Copy project files and set working directory.
5. Define a default command to run the pipeline or start a shell.

Example:
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . ./
CMD ["python", "-m", "pipeline.run"]
```

### 5.7 Optional `docker-compose.yml`
- Define services for the pipeline runner and (optionally) a PostgreSQL database if later needed.
- For a pure SQLite pipeline, compose is optional.

### 5.8 GitHub Actions Workflow
1. Create `.github/workflows/ci.yml`.
2. Workflow steps:
   - Checkout code
   - Set up Python
   - Install dependencies
   - Run `pytest`
   - Optionally build Docker image
3. Example workflow:
```yaml
name: CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: python -m pip install --upgrade pip
      - run: pip install -r requirements.txt
      - run: pytest -q
  docker:
    runs-on: ubuntu-latest
    needs: test
    steps:
      - uses: actions/checkout@v4
      - uses: docker/build-push-action@v4
        with:
          context: .
          tags: user/bank-etl:latest
```

### 5.9 Failure Behavior and Regression Detection
- Configure `pytest` to return non-zero exit code on failures (default behavior).
- CI should fail if any test fails.
- Include `--maxfail=1` for faster failure feedback if desired.
- Add `pytest` coverage reporting (optional) to monitor test coverage.

## 6. Common CI and Container Pitfalls
- **Non-deterministic tests**: avoid reliance on system clock or random data without seeding.
- **Missing dependencies**: pin versions in `requirements.txt` to prevent changing builds.
- **Large data in tests**: keep datasets small to avoid long CI runtime.
- **Permissions issues**: ensure files/directories are writable in container environments.

## 7. Acceptance Criteria
- Unit tests cover key logic in extraction, transformation, validation, and loading.
- Integration test runs end-to-end and validates expected warehouse state.
- Dockerfile builds successfully and can run the pipeline.
- GitHub Actions workflow runs tests on push/pull request.
- Failures in tests or build stop the pipeline (regression detection).

## 8. Definition of Done
- `tests/` contains unit and integration tests and they pass.
- CI pipeline is configured and green on the default branch.
- Docker image builds successfully and can run the pipeline.
- Documentation includes instructions to run tests locally and in CI.
