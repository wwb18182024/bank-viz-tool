"""data_C — reusable data-processing functions for financial scenarios.

Pure pandas helpers used by the chart builders so that every chart reflects a
proper financial aggregation rather than raw rows. Each function is deliberately
small, testable and referenced by the executor's audit trail.
"""
from __future__ import annotations

import pandas as pd


def group_aggregate(df: pd.DataFrame, group_col: str, value_col: str | None, agg: str = "sum") -> pd.DataFrame:
    """Group by group_col and aggregate value_col (count when value_col is None)."""
    if agg not in {"sum", "mean", "count", "min", "max", "median"}:
        raise ValueError(f"Unsupported aggregation: {agg}")
    if value_col is None or agg == "count":
        return df.groupby(group_col, dropna=False).size().rename("count").reset_index()
    if value_col not in df.columns:
        raise ValueError(f"Unknown column: {value_col}")
    result = df.groupby(group_col, dropna=False)[value_col].agg(agg).reset_index()
    result.columns = [group_col, f"{agg}_{value_col}"]
    return result


def bin_values(series: pd.Series, bins: int = 10, strategy: str = "quantile") -> pd.Series:
    """Bin a numeric series into labelled intervals (equal-width or quantile)."""
    series = series.dropna()
    if strategy == "quantile":
        try:
            return pd.qcut(series, q=bins, duplicates="drop")
        except ValueError:
            strategy = "uniform"
    return pd.cut(series, bins=bins)


def top_n(df: pd.DataFrame, column: str, n: int = 10) -> pd.DataFrame:
    """Keep only the top-n most frequent categories of a column (rest labelled Other)."""
    counts = df[column].astype(str).value_counts()
    if len(counts) <= n:
        return df
    keep = set(counts.head(n).index)
    out = df.copy()
    out[column] = out[column].astype(str).where(out[column].astype(str).isin(keep), "Other")
    return out


def correlation_matrix(df: pd.DataFrame) -> pd.DataFrame:
    return df.corr(numeric_only=True)


def apply_filter(df: pd.DataFrame, filter_expr: str) -> pd.DataFrame:
    """Apply a simple filter expression of the form 'col=value', 'col>value' etc."""
    import re

    match = re.match(r"^\s*([A-Za-z0-9_ \-]+?)\s*(>=|<=|!=|>|<|=)\s*(.+?)\s*$", filter_expr)
    if not match:
        raise ValueError(f"Cannot parse filter: {filter_expr!r}")
    col, op, raw = match.groups()
    col = col.strip()
    if col not in df.columns:
        raise ValueError(f"Filter column not found: {col}")
    series = df[col]
    try:
        value = float(raw)
        series_num = pd.to_numeric(series, errors="coerce")
        comparable = series_num
    except ValueError:
        value = raw.strip().strip("'\"")
        comparable = series.astype(str)
    if op == "=":
        return df[comparable == value]
    if op == "!=":
        return df[comparable != value]
    if op == ">":
        return df[comparable > value]
    if op == "<":
        return df[comparable < value]
    if op == ">=":
        return df[comparable >= value]
    return df[comparable <= value]


FUNCTION_DESCRIPTIONS = [
    {"name": "group_aggregate", "desc": "Group rows by a column and compute sum/mean/count/min/max of a value column (e.g. total transaction amount per customer segment)."},
    {"name": "bin_values", "desc": "Bin a numeric column into intervals (equal-width or quantile), e.g. age bands or balance bands."},
    {"name": "top_n", "desc": "Keep the top-n most frequent categories and merge the rest into 'Other'."},
    {"name": "correlation_matrix", "desc": "Pearson correlation between all numeric columns."},
    {"name": "apply_filter", "desc": "Filter rows with a simple condition like 'Churn=1' or 'Balance>50000'."},
]
