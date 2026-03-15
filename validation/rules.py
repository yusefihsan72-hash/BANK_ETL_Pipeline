# validation/rules.py
import pandas as pd
from dataclasses import dataclass, field

@dataclass
class ValidationFailure:
    row_index: int
    rule_name: str
    failure_reason: str

def validate_completeness(df, required_cols):
    failures = []
    for col in required_cols:
        if col not in df.columns:
            continue
        nulls = df[df[col].isna()].index
        for i in nulls:
            failures.append(ValidationFailure(i, "completeness",
                f"missing_required_field:{col}"))
    return failures

def validate_uniqueness(df, key_cols):
    failures = []
    dupes = df[df.duplicated(subset=key_cols, keep=False)].index
    for i in dupes:
        failures.append(ValidationFailure(i, "uniqueness",
            f"duplicate_key:{','.join(key_cols)}"))
    return failures

def validate_range(df, col, min_val=None, max_val=None):
    failures = []
    if col not in df.columns:
        return failures
    if min_val is not None:
        below = df[(df[col].notna()) & (df[col] < min_val)].index
        for i in below:
            failures.append(ValidationFailure(i, "range",
                f"value_below_min:{col}={df.loc[i, col]}<{min_val}"))
    if max_val is not None:
        above = df[(df[col].notna()) & (df[col] > max_val)].index
        for i in above:
            failures.append(ValidationFailure(i, "range",
                f"value_above_max:{col}={df.loc[i, col]}>{max_val}"))
    return failures

def validate_allowed_values(df, col, allowed):
    failures = []
    if col not in df.columns:
        return failures
    invalid = df[df[col].notna() & ~df[col].isin(allowed)].index
    for i in invalid:
        failures.append(ValidationFailure(i, "allowed_values",
            f"invalid_value:{col}={df.loc[i, col]}"))
    return failures