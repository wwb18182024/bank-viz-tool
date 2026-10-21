"""Health endpoint with privacy self-check."""
from __future__ import annotations

from fastapi import APIRouter

from ..config import settings
from ..core import llm_client

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health")
def health():
    local_mode = True
    llm_error = None
    try:
        llm_client.ensure_local_endpoint(settings.OLLAMA_URL)
    except llm_client.LLMError as exc:
        local_mode = False
        llm_error = str(exc)
    reachable = llm_client.ollama_reachable() if local_mode else False
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "local_mode": local_mode,
        "llm_error": llm_error,
        "ollama": {
            "url": settings.OLLAMA_URL,
            "reachable": reachable,
            "model": settings.OLLAMA_MODEL,
        },
        "degraded_mode": not reachable,
    }
