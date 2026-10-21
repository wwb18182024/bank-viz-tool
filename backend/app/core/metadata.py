"""data_A — dataset metadata extraction.

Produces a structured profile of the uploaded dataset: per-column semantic type,
missing-value statistics, unique counts, ranges and top values. Only this metadata
(never raw rows) is shared with the LLM.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from ..config import settings

NUMERIC = "numeric"
CATEGORICAL = "categorical"
DATETIME = "datetime"
BOOLEAN = "boolean"
IDENTIFIER = "identifier"
MIXED = "mixed"

_ID_NAME_HINTS = ("id", "uuid", "guid", "ssn", "account_no", "customer_id", "rownum")


def _looks_like_identifier(name: str, series: pd.Series) -> bool:
    n = len(series)
    if n == 0:
        return False
    unique_ratio = series.nunique(dropna=True) / n
    name_hit = any(h in name.lower().replace(" ", "_") for h in _ID_NAME_HINTS)
    if pd.api.types.is_float_dtype(series):
        # Continuous measures (balances, amounts) are unique-ish by nature:
        # never classify as identifier on cardinality alone.
        return name_hit and unique_ratio > 0.9
    return (name_hit and unique_ratio > 0.9) or unique_ratio > 0.98


def infer_semantic_type(name: str, series: pd.Series) -> str:
    if pd.api.types.is_bool_dtype(series):
        return BOOLEAN
    if pd.api.types.is_numeric_dtype(series):
        if _looks_like_identifier(name, series):
            return IDENTIFIER
        # Integer columns with exactly two values (e.g. churn flags 0/1) are
        # semantically boolean, not measures.
        if (
            pd.api.types.is_integer_dtype(series)
            and series.dropna().nunique() == 2
            and len(series.dropna()) >= 10
        ):
            return BOOLEAN
        return NUMERIC
    if pd.api.types.is_datetime64_any_dtype(series):
        return DATETIME
    non_null = series.dropna()
    if non_null.empty:
        return MIXED
    # Try datetime inference on object columns
    if non_null.dtype == object:
        sample = non_null.astype(str).head(200)
        try:
            parsed = pd.to_datetime(sample, errors="raise", format="mixed")
            if parsed.notna().mean() > 0.9:
                return DATETIME
        except (ValueError, TypeError, pd.errors.OutOfBoundsDatetime):
            pass
    if _looks_like_identifier(name, series):
        return IDENTIFIER
    return CATEGORICAL


def profile_column(name: str, series: pd.Series, semantic_type: str) -> dict:
    non_null = series.dropna()
    info: dict = {
        "name": name,
        "dtype": str(series.dtype),
        "semantic_type": semantic_type,
        "missing": int(series.isna().sum()),
        "missing_pct": round(float(series.isna().mean()) * 100, 2),
        "unique": int(series.nunique(dropna=True)),
    }
    if semantic_type == NUMERIC:
        desc = non_null.describe()
        info.update(
            min=_safe(desc.get("min")),
            max=_safe(desc.get("max")),
            mean=_safe(desc.get("mean")),
            std=_safe(desc.get("std")),
            p25=_safe(desc.get("25%")),
            p50=_safe(desc.get("50%")),
            p75=_safe(desc.get("75%")),
        )
    elif semantic_type == DATETIME and not non_null.empty:
        parsed = pd.to_datetime(non_null, errors="coerce")
        info.update(min=str(parsed.min()), max=str(parsed.max()))
    elif semantic_type in (CATEGORICAL, BOOLEAN):
        top = non_null.astype(str).value_counts().head(settings.TOP_K_CATEGORIES)
        info["top_values"] = [{"value": v, "count": int(c)} for v, c in top.items()]
    return info


def _safe(value):
    if value is None or (isinstance(value, float) and (np.isnan(value) or np.isinf(value))):
        return None
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return round(float(value), 4)
    return value


def extract_metadata(df: pd.DataFrame) -> dict:
    columns = []
    for name in df.columns:
        series = df[name]
        stype = infer_semantic_type(str(name), series)
        columns.append(profile_column(str(name), series, stype))
    return {
        "n_rows": int(len(df)),
        "n_columns": int(len(df.columns)),
        "columns": columns,
    }


def columns_by_type(meta: dict) -> dict:
    """Convenience view of metadata used by prompt builders and validators."""
    by_type = {NUMERIC: [], CATEGORICAL: [], DATETIME: [], BOOLEAN: [], IDENTIFIER: []}
    for col in meta["columns"]:
        by_type.setdefault(col["semantic_type"], []).append(col["name"])
    return by_type


def column_map(meta: dict) -> dict:
    return {col["name"]: col for col in meta["columns"]}
