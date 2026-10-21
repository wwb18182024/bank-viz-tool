"""Plan executor: validated ChartSpecs -> chart JSON via data_B + data_C."""
from __future__ import annotations

import pandas as pd

from . import chart_registry


def execute_spec(df: pd.DataFrame, spec, meta: dict) -> dict:
    """Execute one spec. Returns {ok, option, functions_used} or {ok, error}."""
    try:
        entry = chart_registry.REGISTRY[spec.chart_type]
        option, used = entry["builder"](df, spec, meta)
        return {"ok": True, "option": option, "functions_used": used}
    except chart_registry.ChartError as exc:
        return {"ok": False, "error": str(exc)}
    except Exception as exc:  # noqa: BLE001 — one bad chart must not kill the batch
        return {"ok": False, "error": f"Rendering failed: {exc}"}


def execute_plan(df: pd.DataFrame, specs: list, meta: dict) -> list[dict]:
    results = []
    for spec in specs:
        result = execute_spec(df, spec, meta)
        results.append({
            "spec": spec.model_dump(),
            "rationale": spec.rationale,
            **result,
        })
    return results
