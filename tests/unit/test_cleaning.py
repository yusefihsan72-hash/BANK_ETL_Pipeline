# tests/unit/test_cleaning.py
import pandas as pd
import pytest
from transformation.cleaning import drop_missing_keys, deduplicate

def test_drop_missing_customer_id():
    df = pd.DataFrame({"customer_id": ["c1", None, "c2"], "age": [30, 25, 40]})
    result = drop_missing_keys(df, ["customer_id"])
    assert len(result) == 2
    assert "c1" in result["customer_id"].values

def test_deduplicate_keeps_first():
    df = pd.DataFrame({
        "transaction_id": ["t1", "t1", "t2"],
        "amount": [100, 200, 300]
    })
    result = deduplicate(df, ["transaction_id"])
    assert len(result) == 2
    assert result[result["transaction_id"] == "t1"]["amount"].values[0] == 100

# tests/unit/test_validation.py
from validation.rules import validate_completeness, validate_range

def test_validate_missing_required():
    df = pd.DataFrame({"customer_id": ["c1", None], "age": [30, 25]})
    failures = validate_completeness(df, ["customer_id"])
    assert len(failures) == 1
    assert "missing_required_field:customer_id" in failures[0].failure_reason

def test_validate_age_range():
    df = pd.DataFrame({"age": [25, -1, 150, 45]})
    failures = validate_range(df, "age", 18, 120)
    assert len(failures) == 2