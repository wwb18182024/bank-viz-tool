"""Automatic visualisation endpoints: LLM plan -> validation/filter -> execution."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from ..core import executor, fallback_recommender, llm_client, plan_validator
from ..core.session_store import store

router = APIRouter(prefix="/api/autoviz", tags=["autoviz"])


def _session_or_404(dataset_id: str):
    session = store.get(dataset_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Dataset session not found")
    return session


@router.post("/{dataset_id}/plan")
def generate_plan(dataset_id: str):
    """Produce a validated, domain-filtered visualisation plan (no rendering)."""
    session = _session_or_404(dataset_id)
    from ..core.metadata import extract_metadata

    meta = extract_metadata(session.df)
    degraded = False
    try:
        specs = llm_client.call_llm(meta)
        source = "llm"
    except llm_client.LLMError:
        specs = fallback_recommender.recommend_plan(meta)
        source = "fallback"
        degraded = True
    accepted, rejected = plan_validator.filter_plan(specs, meta)
    if not accepted:
        specs = fallback_recommender.recommend_plan(meta)
        accepted, rejected = plan_validator.filter_plan(specs, meta)
        source, degraded = "fallback", True
    return {
        "source": source,
        "degraded": degraded,
        "plan": [s.model_dump() for s in accepted],
        "rejected": rejected,
    }


@router.post("/{dataset_id}/execute")
def execute_plan(dataset_id: str, body: dict | None = None):
    """Execute a plan: body = {"charts": [spec, ...]}. If omitted, generates one."""
    session = _session_or_404(dataset_id)
    from ..core.metadata import extract_metadata
    from ..core.plan_schema import parse_plan

    meta = extract_metadata(session.df)
    if body and body.get("charts"):
        specs = parse_plan(body)
    else:
        try:
            specs = llm_client.call_llm(meta)
        except llm_client.LLMError:
            specs = fallback_recommender.recommend_plan(meta)
        specs, _ = plan_validator.filter_plan(specs, meta)
        if not specs:
            specs, _ = plan_validator.filter_plan(fallback_recommender.recommend_plan(meta), meta)
    results = executor.execute_plan(session.df, specs, meta)
    session.history.append({"mode": "auto", "n_charts": sum(1 for r in results if r["ok"])})
    return {
        "degraded": False,
        "charts": results,
    }
