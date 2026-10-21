"""Manual chart customisation endpoints."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from ..core import chart_registry, executor, plan_validator
from ..core.metadata import extract_metadata
from ..core.plan_schema import ChartSpec
from ..core.session_store import store

router = APIRouter(prefix="/api/manual", tags=["manual"])


def _session_or_404(dataset_id: str):
    session = store.get(dataset_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Dataset session not found")
    return session


@router.get("/{dataset_id}/options")
def chart_options(dataset_id: str):
    """Populate the manual builder UI: chart types + typed column lists."""
    session = _session_or_404(dataset_id)
    meta = extract_metadata(session.df)
    return {
        "chart_types": chart_registry.library_descriptions(),
        "columns": meta["columns"],
    }


@router.post("/{dataset_id}/chart")
def build_chart(dataset_id: str, spec: ChartSpec):
    """Build one user-specified chart through the same engine as auto mode."""
    session = _session_or_404(dataset_id)
    meta = extract_metadata(session.df)
    ok, reason = plan_validator.validate_spec(spec, meta)
    if not ok:
        raise HTTPException(status_code=422, detail=reason)
    result = executor.execute_spec(session.df, spec, meta)
    session.history.append({"mode": "manual", "chart": spec.title})
    return {"spec": spec.model_dump(), **result}
