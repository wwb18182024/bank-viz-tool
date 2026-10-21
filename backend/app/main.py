"""BankViz FastAPI application entry point."""
from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api import routes_autoviz, routes_dataset, routes_health, routes_manual
from .config import settings
from .core import llm_client

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("bankviz")

app = FastAPI(title=settings.APP_NAME, version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(routes_dataset.router)
app.include_router(routes_autoviz.router)
app.include_router(routes_manual.router)
app.include_router(routes_health.router)


@app.on_event("startup")
def startup_privacy_check():
    """Fail closed on remote LLM endpoints; warn (but continue in degraded mode)
    if the local LLM is simply not running yet."""
    llm_client.ensure_local_endpoint(settings.OLLAMA_URL)
    if llm_client.ollama_reachable():
        logger.info("Local LLM detected at %s (model: %s)", settings.OLLAMA_URL, settings.OLLAMA_MODEL)
    else:
        logger.warning(
            "Ollama not reachable at %s — starting in DEGRADED MODE (statistical fallback recommender). "
            "Start Ollama and pull model '%s' for full functionality.",
            settings.OLLAMA_URL, settings.OLLAMA_MODEL,
        )
