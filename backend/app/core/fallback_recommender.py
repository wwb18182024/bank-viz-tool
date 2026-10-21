"""Statistical fallback recommender — used when the LLM is unreachable or
produces no valid plan (degraded mode). Deterministic, domain-aware defaults.
"""
from __future__ import annotations

from .metadata import BOOLEAN, CATEGORICAL, DATETIME, IDENTIFIER, NUMERIC, columns_by_type
from .plan_schema import ChartSpec


def _first(cols: list, exclude: set) -> str | None:
    for c in cols:
        if c not in exclude:
            return c
    return None


def recommend_plan(meta: dict) -> list[ChartSpec]:
    by_type = columns_by_type(meta)
    numeric = list(by_type[NUMERIC])
    categorical = list(by_type[CATEGORICAL] + by_type[BOOLEAN])
    datetime_cols = list(by_type[DATETIME])
    identifiers = list(by_type[IDENTIFIER])
    used: set = set(identifiers)
    specs: list[ChartSpec] = []

    # 1. Target-like binary/categorical column (churn, risk, default...) → pie
    target = next(
        (c for c in categorical if any(k in c.lower() for k in ("churn", "risk", "default", "exit", "status"))),
        None,
    )
    if target:
        specs.append(ChartSpec(
            chart_type="pie", x=target, agg="count",
            title=f"Customer distribution by {target}",
            rationale=f"Proportion of customers per {target} — baseline for churn/risk analysis",
        ))
        used.add(target)

    # 2. Key numeric distributions (prioritise financial-sounding columns)
    key_numeric = sorted(
        numeric,
        key=lambda c: any(k in c.lower() for k in ("balance", "amount", "transaction", "credit", "income", "salary", "age")),
        reverse=True,
    )
    for col in key_numeric[:2]:
        specs.append(ChartSpec(
            chart_type="histogram", x=col, agg="count", bins=20,
            title=f"Distribution of {col}",
            rationale=f"Skew and outliers of {col} reveal customer risk exposure",
        ))

    # 3. Category vs numeric → bar of mean (segmentation)
    for cat in categorical[:2]:
        num = _first(key_numeric, {s.x for s in specs} | used)
        if cat and num and num != cat:
            specs.append(ChartSpec(
                chart_type="bar", x=cat, y=num, agg="mean",
                title=f"Average {num} by {cat}",
                rationale=f"Customer segmentation: {num} behaviour across {cat}",
            ))
            used.add(cat)

    # 4. Box plot: numeric spread across target/category (risk analysis)
    if target and numeric:
        num = _first(key_numeric, {s.x for s in specs})
        if num:
            specs.append(ChartSpec(
                chart_type="box", x=target, y=num, agg="count",
                title=f"{num} distribution by {target}",
                rationale=f"Risk analysis: spread of {num} differs between {target} groups",
            ))

    # 5. Two most interesting numeric columns → scatter (transaction behaviour)
    if len(key_numeric) >= 2:
        a, b = key_numeric[0], key_numeric[1]
        if a != b:
            specs.append(ChartSpec(
                chart_type="scatter", x=a, y=b, agg="count",
                group=target if target in categorical else None,
                title=f"{a} vs {b}" + (f" by {target}" if target in categorical else ""),
                rationale="Transaction behaviour: relationship between two key financial variables",
            ))

    # 6. Correlation heatmap (risk drivers)
    if len(numeric) >= 3:
        specs.append(ChartSpec(
            chart_type="heatmap", agg="count",
            title="Correlation heatmap of numeric variables",
            rationale="Risk drivers: which financial variables move together",
        ))

    # 7. Grouped bar: category split by target (product adoption / retention)
    if target:
        cat = _first([c for c in categorical if c != target and c not in used], set())
        if cat:
            specs.append(ChartSpec(
                chart_type="grouped_bar", x=cat, agg="count", group=target,
                title=f"{cat} composition by {target}",
                rationale=f"Product adoption/retention: how {cat} differs across {target} groups",
            ))

    # 8. Time trend if datetime exists
    if datetime_cols and numeric:
        num = key_numeric[0]
        specs.append(ChartSpec(
            chart_type="line", x=datetime_cols[0], y=num, agg="mean",
            title=f"{num} over {datetime_cols[0]}",
            rationale="Transaction behaviour trend over time",
        ))

    return specs[:8]
