"""Structured schema for LLM-generated visualisation plans (data contract)."""
from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field, ValidationError


AggFunc = Literal["sum", "mean", "count", "min", "max", "median"]


class ChartSpec(BaseModel):
    chart_type: str
    title: str = Field(min_length=1, max_length=120)
    rationale: str = ""
    x: Optional[str] = None
    y: Optional[str] = None
    group: Optional[str] = None
    agg: AggFunc = "count"
    bins: Optional[int] = Field(default=None, ge=2, le=100)
    filter: Optional[str] = None

    def key(self) -> tuple:
        """Identity key used for de-duplication."""
        return (self.chart_type, self.x, self.y, self.group, self.agg, self.filter)


class VisPlan(BaseModel):
    charts: list[ChartSpec]


def parse_plan(raw: dict | list) -> list[ChartSpec]:
    """Parse an LLM plan payload into ChartSpecs, skipping malformed entries.

    Accepts {"charts": [...]}, {"plan": [...]}, or a bare list.
    """
    if isinstance(raw, list):
        items = raw
    elif isinstance(raw, dict):
        items = raw.get("charts") or raw.get("plan") or raw.get("visualizations") or []
    else:
        return []
    specs = []
    for item in items:
        if not isinstance(item, dict):
            continue
        # Normalise common LLM synonyms
        item = dict(item)
        if "type" in item and "chart_type" not in item:
            item["chart_type"] = item.pop("type")
        if "x_axis" in item and "x" not in item:
            item["x"] = item.pop("x_axis")
        if "y_axis" in item and "y" not in item:
            item["y"] = item.pop("y_axis")
        if "agg" in item and isinstance(item["agg"], str):
            item["agg"] = item["agg"].lower()
        try:
            specs.append(ChartSpec(**{k: v for k, v in item.items() if k in ChartSpec.model_fields}))
        except ValidationError:
            continue
    return specs
