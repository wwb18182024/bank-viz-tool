"""Domain-aware validation and filtering of chart plans (two-layer rule engine).

Layer 1 (soft): banking-domain instructions inside the LLM prompt.
Layer 2 (hard): the deterministic rules in this module — always enforced,
regardless of what the LLM produced.
"""
from __future__ import annotations

from . import chart_registry
from .metadata import CATEGORICAL, DATETIME, IDENTIFIER, BOOLEAN, column_map

# Banking themes whose presence in a chart's rationale/title raises its rank.
BANKING_THEMES = (
    "churn", "segment", "transaction", "risk", "credit", "loan", "balance",
    "product", "adoption", "retention", "revenue", "exposure", "default",
    "geograph", "age", "income", "complain", "fraud",
)

MAX_CATEGORY_CARDINALITY = 30
MAX_PIE_CARDINALITY = 20

THEME_PRIORITY = 100
STANDARD_PRIORITY = 0


def _cardinality(col: dict) -> int:
    return col.get("unique") or 0


def validate_spec(spec, meta: dict) -> tuple[bool, str]:
    """Return (ok, reason). Hard rules — a failing spec must not be rendered."""
    if spec.chart_type not in chart_registry.REGISTRY:
        return False, f"Unknown chart type: {spec.chart_type}"
    cmap = column_map(meta)
    signature = chart_registry.REGISTRY[spec.chart_type]["signature"]

    # Column existence
    for role in ("x", "y", "group"):
        col = getattr(spec, role)
        if col is not None and col not in cmap:
            return False, f"{role.upper()} column not found: {col}"

    # Identifier columns must never appear on axes
    for role in ("x", "y", "group"):
        col = getattr(spec, role)
        if col and cmap[col]["semantic_type"] == IDENTIFIER:
            return False, f"Identifier column '{col}' is not allowed on {role.upper()}"

    # Per-chart-type structural rules
    def _num(col):
        return cmap[col]["semantic_type"] in ("numeric", "datetime") if col else False

    def _cat(col):
        return cmap[col]["semantic_type"] in (CATEGORICAL, BOOLEAN) if col else False

    if spec.chart_type == "scatter":
        if not (_num(spec.x) and _num(spec.y)):
            return False, "Scatter plot requires two numeric columns"
    elif spec.chart_type == "histogram":
        if not _num(spec.x):
            return False, "Histogram requires a numeric column on X"
    elif spec.chart_type == "box":
        if not _num(spec.y):
            return False, "Box plot requires a numeric Y column"
        if spec.x and not (_cat(spec.x) or _num(spec.x)):
            return False, "Box plot X must be categorical"
    elif spec.chart_type in ("bar", "pie", "line"):
        if not (spec.x and (_cat(spec.x) or _num(spec.x))):
            return False, f"{spec.chart_type} requires an X column"
        if spec.y is not None and not _num(spec.y):
            return False, f"{spec.chart_type} Y must be numeric (or omitted for count)"
    elif spec.chart_type in ("grouped_bar", "stacked_bar"):
        if not (spec.x and _cat(spec.x)):
            return False, "Grouped/stacked bar requires a categorical X"
        if spec.group and not _cat(spec.group):
            return False, "Grouped/stacked bar group must be categorical"
    elif spec.chart_type == "heatmap":
        pass

    # Cardinality guards: meaningless charts of too many categories
    if spec.chart_type == "pie" and spec.x and _cardinality(cmap[spec.x]) > MAX_PIE_CARDINALITY:
        return False, f"Pie chart with >{MAX_PIE_CARDINALITY} categories is unreadable (use bar)"
    if spec.chart_type in ("bar", "line") and spec.x and _cat(spec.x) and _cardinality(cmap[spec.x]) > MAX_CATEGORY_CARDINALITY and (spec.y is None or spec.agg == "count"):
        return False, f"Counting {cmap[spec.x]['unique']} categories is meaningless"

    if signature and spec.chart_type in ("grouped_bar", "stacked_bar") and not spec.group:
        return False, "Grouped/stacked bar requires a group variable"

    return True, "ok"


def theme_score(spec) -> int:
    text = f"{spec.title} {spec.rationale}".lower()
    return sum(1 for theme in BANKING_THEMES if theme in text)


def rank_specs(specs: list) -> list:
    """Sort charts: banking-relevant first, then fewer variables first."""
    return sorted(specs, key=lambda s: (-theme_score(s), len([v for v in (s.x, s.y, s.group) if v])))


def dedupe(specs: list) -> list:
    seen, out = set(), []
    for s in specs:
        k = s.key()
        if k not in seen:
            seen.add(k)
            out.append(s)
    return out


def filter_plan(specs: list, meta: dict) -> tuple[list, list]:
    """Returns (accepted, rejected) where rejected = [{spec, reason}]."""
    accepted, rejected = [], []
    for spec in dedupe(specs):
        ok, reason = validate_spec(spec, meta)
        if ok:
            accepted.append(spec)
        else:
            rejected.append({"spec": spec.model_dump(), "reason": reason})
    return rank_specs(accepted), rejected
