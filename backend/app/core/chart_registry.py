"""data_B — pre-coded visualisation components (chart library).

Each registry entry provides an id, a human-readable description and an input
signature (used both for validation and for the LLM prompt), plus a pure builder
function: (DataFrame, ChartSpec) -> ECharts-compatible option dict.

Builders never mutate the input DataFrame and never emit raw row data beyond
what the aggregation implies.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import processing

MAX_SCATTER_POINTS = 2000
MAX_PIE_SLICES = 8
MAX_BAR_CATEGORIES = 30
MAX_BOX_GROUPS = 12
MAX_SERIES_GROUPS = 6


class ChartError(ValueError):
    pass


# ---------------------------------------------------------------- helpers

def _is_categorical(meta: dict, col: str) -> bool:
    cmap = {c["name"]: c for c in meta["columns"]}
    return col in cmap and cmap[col]["semantic_type"] in ("categorical", "boolean")


def _agg_column(df: pd.DataFrame, spec) -> tuple[list, list, list]:
    """Return (labels, values, functions_used) for a categorical-x / value-y chart."""
    used = ["group_aggregate"]
    work = df
    if spec.filter:
        work = processing.apply_filter(work, spec.filter)
        used.append("apply_filter")
    x = spec.x
    if work[x].nunique() > MAX_BAR_CATEGORIES:
        work = processing.top_n(work, x, MAX_BAR_CATEGORIES)
        used.append("top_n")
    if spec.y is None or spec.agg == "count":
        counts = work[x].astype(str).value_counts()
        used = ["group_aggregate(count)"] + [u for u in used if u != "group_aggregate"]
        return counts.index.tolist(), counts.tolist(), used
    g = processing.group_aggregate(work, x, spec.y, spec.agg)
    g = g.sort_values(g.columns[1], ascending=False)
    value_col = g.columns[1]
    return g[x].astype(str).tolist(), g[value_col].tolist(), used


def _axis_category(name: str) -> dict:
    return {"type": "category", "name": name}


def _axis_value(name: str | None = None) -> dict:
    return {"type": "value", "name": name or ""}


def _base(title: str) -> dict:
    return {
        "title": {"text": title, "left": "center", "textStyle": {"fontSize": 14}},
        "tooltip": {"trigger": "auto"},
        "legend": {"bottom": 0},
    }


# ---------------------------------------------------------------- builders

def build_bar(df: pd.DataFrame, spec, meta: dict) -> dict:
    labels, values, used = _agg_column(df, spec)
    return {
        **_base(spec.title),
        "xAxis": {**_axis_category(spec.x), "data": labels, "axisLabel": {"rotate": 30 if len(labels) > 8 else 0}},
        "yAxis": _axis_value(spec.y or "Count"),
        "series": [{"type": "bar", "data": values, "name": spec.y or "Count"}],
        "legend": {"show": False},
    }, used


def _grouped_pivot(df: pd.DataFrame, spec, used: list) -> pd.DataFrame:
    """Shared aggregation for grouped/stacked charts: index=x, columns=group."""
    work = df
    if spec.filter:
        work = processing.apply_filter(work, spec.filter)
        used.append("apply_filter")
    if work[spec.group].nunique() > MAX_SERIES_GROUPS:
        work = processing.top_n(work, spec.group, MAX_SERIES_GROUPS)
    if work[spec.x].nunique() > MAX_BAR_CATEGORIES:
        work = processing.top_n(work, spec.x, MAX_BAR_CATEGORIES)
    if spec.y is None or spec.agg == "count":
        pivot = work.pivot_table(index=spec.x, columns=spec.group, aggfunc="size", fill_value=0)
    else:
        pivot = work.pivot_table(index=spec.x, columns=spec.group, values=spec.y, aggfunc=spec.agg, fill_value=0)
    return pivot.loc[pivot.sum(axis=1).sort_values(ascending=False).index[:MAX_BAR_CATEGORIES]]


def build_grouped_bar(df: pd.DataFrame, spec, meta: dict, stacked: bool = False) -> dict:
    used = ["group_aggregate", "top_n"]
    pivot = _grouped_pivot(df, spec, used)
    labels = pivot.index.astype(str).tolist()
    series = [
        {"name": str(c), "type": "bar", "stack": "total" if stacked else None, "data": [None if pd.isna(v) else round(float(v), 4) for v in pivot[c]]}
        for c in pivot.columns
    ]
    return {
        **_base(spec.title),
        "xAxis": {**_axis_category(spec.x), "data": labels, "axisLabel": {"rotate": 30 if len(labels) > 8 else 0}},
        "yAxis": _axis_value(spec.y or "Count"),
        "series": series,
    }, used


def build_stacked_area(df: pd.DataFrame, spec, meta: dict) -> dict:
    used = ["group_aggregate", "top_n"]
    pivot = _grouped_pivot(df, spec, used)
    labels = pivot.index.astype(str).tolist()
    series = [
        {"name": str(c), "type": "line", "stack": "total", "areaStyle": {},
         "data": [None if pd.isna(v) else round(float(v), 4) for v in pivot[c]]}
        for c in pivot.columns
    ]
    return {
        **_base(spec.title),
        "xAxis": {**_axis_category(spec.x), "data": labels, "axisLabel": {"rotate": 30 if len(labels) > 8 else 0}},
        "yAxis": _axis_value(spec.y or "Count"),
        "series": series,
    }, used


def build_horizontal_bar(df: pd.DataFrame, spec, meta: dict) -> dict:
    labels, values, used = _agg_column(df, spec)
    return {
        **_base(spec.title),
        "xAxis": _axis_value(spec.y or "Count"),
        "yAxis": {**_axis_category(spec.x), "data": labels},
        "series": [{"type": "bar", "data": values, "name": spec.y or "Count"}],
        "legend": {"show": False},
    }, used


def build_pie(df: pd.DataFrame, spec, meta: dict, donut: bool = False) -> dict:
    labels, values, used = _agg_column(df, spec)
    if len(labels) > MAX_PIE_SLICES:
        labels, values = labels[:MAX_PIE_SLICES], values[:MAX_PIE_SLICES]
        labels.append("Other")
        values.append(max(0, int(df[spec.x].nunique()) - MAX_PIE_SLICES))
        used.append("top_n")
    radius = ["45%", "68%"] if donut else "62%"
    return {
        **_base(spec.title),
        "series": [{"type": "pie", "radius": radius, "data": [{"name": str(l), "value": v} for l, v in zip(labels, values)]}],
        "legend": {"bottom": 0, "type": "scroll"},
    }, used


def build_histogram(df: pd.DataFrame, spec, meta: dict) -> dict:
    used = ["bin_values"]
    work = df
    if spec.filter:
        work = processing.apply_filter(work, spec.filter)
        used.append("apply_filter")
    series = pd.to_numeric(work[spec.x], errors="coerce").dropna()
    if series.empty:
        raise ChartError(f"Column {spec.x} has no numeric values")
    bins = spec.bins or 20
    counts, edges = np.histogram(series, bins=bins)
    labels = [f"{edges[i]:.1f}–{edges[i+1]:.1f}" for i in range(len(counts))]
    return {
        **_base(spec.title),
        "xAxis": {**_axis_category(spec.x), "data": labels, "axisLabel": {"rotate": 40, "fontSize": 10}},
        "yAxis": _axis_value("Frequency"),
        "series": [{"type": "bar", "data": counts.tolist(), "name": "Frequency"}],
        "legend": {"show": False},
    }, used


def build_box(df: pd.DataFrame, spec, meta: dict) -> dict:
    used = ["group_aggregate(stats)"]
    work = df
    if spec.filter:
        work = processing.apply_filter(work, spec.filter)
        used.append("apply_filter")
    y = pd.to_numeric(work[spec.y], errors="coerce").dropna()
    if y.empty:
        raise ChartError(f"Column {spec.y} has no numeric values")
    if spec.x:
        work = work.assign(_y=y.reindex(work.index))
        if work[spec.x].nunique() > MAX_BOX_GROUPS:
            work = processing.top_n(work, spec.x, MAX_BOX_GROUPS)
            used.append("top_n")
        groups = []
        labels = []
        for cat, sub in work.groupby(spec.x, observed=True):
            vals = pd.to_numeric(sub["_y"], errors="coerce").dropna()
            if vals.empty:
                continue
            q1, med, q3 = vals.quantile([0.25, 0.5, 0.75])
            groups.append([float(vals.min()), float(q1), float(med), float(q3), float(vals.max())])
            labels.append(str(cat))
        if not groups:
            raise ChartError("No data available for box plot")
    else:
        q1, med, q3 = y.quantile([0.25, 0.5, 0.75])
        groups = [[float(y.min()), float(q1), float(med), float(q3), float(y.max())]]
        labels = [spec.y]
    return {
        **_base(spec.title),
        "xAxis": {**_axis_category(spec.x or ""), "data": labels},
        "yAxis": _axis_value(spec.y),
        "series": [{"type": "boxplot", "data": groups, "name": spec.y}],
        "legend": {"show": False},
    }, used


def build_scatter(df: pd.DataFrame, spec, meta: dict) -> dict:
    used = ["apply_filter"] if spec.filter else []
    work = df
    if spec.filter:
        work = processing.apply_filter(work, spec.filter)
    x = pd.to_numeric(work[spec.x], errors="coerce")
    y = pd.to_numeric(work[spec.y], errors="coerce")
    mask = x.notna() & y.notna()
    x, y = x[mask], y[mask]
    if x.empty:
        raise ChartError(f"No numeric pairs for {spec.x} vs {spec.y}")
    if len(x) > MAX_SCATTER_POINTS:
        idx = np.random.default_rng(42).choice(len(x), MAX_SCATTER_POINTS, replace=False)
        x, y = x.iloc[idx], y.iloc[idx]
        used.append(f"sample(n={MAX_SCATTER_POINTS})")
    if spec.group and work.loc[x.index, spec.group].nunique() <= MAX_SERIES_GROUPS:
        gvals = work.loc[x.index, spec.group].astype(str)
        series = [
            {"name": g, "type": "scatter", "data": [[float(a), float(b)] for a, b in zip(x[gvals == g], y[gvals == g])]}
            for g in sorted(gvals.unique())
        ]
    else:
        series = [{"type": "scatter", "data": [[float(a), float(b)] for a, b in zip(x, y)], "name": f"{spec.x} vs {spec.y}"}]
    return {
        **_base(spec.title),
        "xAxis": {**_axis_value(spec.x), "scale": True},
        "yAxis": {**_axis_value(spec.y), "scale": True},
        "series": series,
        "tooltip": {"trigger": "item"},
    }, used


def build_line(df: pd.DataFrame, spec, meta: dict) -> dict:
    labels, values, used = _agg_column(df, spec)
    return {
        **_base(spec.title),
        "xAxis": {**_axis_category(spec.x), "data": labels},
        "yAxis": _axis_value(spec.y or "Count"),
        "series": [{"type": "line", "data": values, "name": spec.y or "Count", "smooth": True}],
        "legend": {"show": False},
    }, used


def build_heatmap(df: pd.DataFrame, spec, meta: dict) -> dict:
    corr = processing.correlation_matrix(df)
    used = ["correlation_matrix"]
    cols = list(corr.columns)
    data = [
        [i, j, round(float(corr.iloc[i, j]), 3)]
        for i in range(len(cols))
        for j in range(len(cols))
        if not pd.isna(corr.iloc[i, j])
    ]
    if not data:
        raise ChartError("Not enough numeric columns for a correlation heatmap")
    return {
        **_base(spec.title or "Correlation heatmap of numeric variables"),
        "tooltip": {"position": "inside"},
        "xAxis": {"type": "category", "data": cols, "axisLabel": {"rotate": 40, "fontSize": 10}},
        "yAxis": {"type": "category", "data": cols},
        "visualMap": {
            "min": -1, "max": 1, "calculable": True, "orient": "horizontal",
            "left": "center", "bottom": 0,
            "inRange": {"color": ["#378ADD", "#FFFFFF", "#D85A30"]},
        },
        "series": [{"type": "heatmap", "data": data, "label": {"show": len(cols) <= 10}}],
        "legend": {"show": False},
        "grid": {"bottom": 90},
    }, used


REGISTRY: dict[str, dict] = {
    "bar": {
        "name": "Bar chart",
        "description": "Compare a value across categories, e.g. average balance per geography, or customer counts per churn status.",
        "signature": "categorical x, optional numeric y (aggregated)",
        "builder": build_bar,
    },
    "grouped_bar": {
        "name": "Grouped bar chart",
        "description": "Compare a value across categories split by a second categorical variable, e.g. churn rate per product per geography.",
        "signature": "categorical x, numeric y (aggregated), categorical group",
        "builder": lambda df, spec, meta: build_grouped_bar(df, spec, meta, stacked=False),
    },
    "stacked_bar": {
        "name": "Stacked bar chart",
        "description": "Composition of a category by a second variable, e.g. product adoption split by customer segment.",
        "signature": "categorical x, numeric y (aggregated), categorical group",
        "builder": lambda df, spec, meta: build_grouped_bar(df, spec, meta, stacked=True),
    },
    "pie": {
        "name": "Pie chart",
        "description": "Show proportions of a low-cardinality category, e.g. share of customers by churn label.",
        "signature": "categorical x (few categories), optional numeric y",
        "builder": build_pie,
    },
    "donut": {
        "name": "Donut chart",
        "description": "Proportions of a low-cardinality category with a hole for a centred KPI, e.g. portfolio mix by product.",
        "signature": "categorical x (few categories), optional numeric y",
        "builder": lambda df, spec, meta: build_pie(df, spec, meta, donut=True),
    },
    "horizontal_bar": {
        "name": "Horizontal bar chart",
        "description": "Ranked comparison across many or long-named categories, e.g. top product categories by total transaction amount.",
        "signature": "categorical x, optional numeric y (aggregated)",
        "builder": build_horizontal_bar,
    },
    "stacked_area": {
        "name": "Stacked area chart",
        "description": "Composition trend over an ordered variable, e.g. monthly transaction volume split by product.",
        "signature": "ordered/categorical x, numeric y (aggregated), categorical group",
        "builder": build_stacked_area,
    },
    "histogram": {
        "name": "Histogram",
        "description": "Show the distribution of a numeric variable, e.g. account balance distribution or transaction amounts.",
        "signature": "numeric x, optional bins",
        "builder": build_histogram,
    },
    "box": {
        "name": "Box plot",
        "description": "Compare the distribution/spread of a numeric variable across categories, e.g. credit limit by risk category — good for risk analysis.",
        "signature": "numeric y, optional categorical x",
        "builder": build_box,
    },
    "scatter": {
        "name": "Scatter plot",
        "description": "Relationship between two numeric variables, e.g. balance vs transaction count, coloured by churn.",
        "signature": "numeric x, numeric y, optional categorical group",
        "builder": build_scatter,
    },
    "line": {
        "name": "Line chart",
        "description": "Trend of a value across an ordered (often temporal) variable, e.g. monthly transaction volume.",
        "signature": "ordered/datetime x, numeric y",
        "builder": build_line,
    },
    "heatmap": {
        "name": "Correlation heatmap",
        "description": "Correlation between all numeric variables at once — reveals risk and behaviour drivers.",
        "signature": "no axes (all numeric columns)",
        "builder": build_heatmap,
    },
}


def library_descriptions() -> list[dict]:
    """Machine-readable library description passed to the LLM (data_B)."""
    return [
        {"id": cid, "name": entry["name"], "usage": entry["description"], "input": entry["signature"]}
        for cid, entry in REGISTRY.items()
    ]
