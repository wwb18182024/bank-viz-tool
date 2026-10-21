"""Local LLM client (Ollama). Privacy-critical module:

- The endpoint must be local (localhost/127.0.0.1/::1) — remote endpoints are
  refused at startup (fail closed).
- Prompts contain dataset METADATA only, never raw rows.
"""
from __future__ import annotations

import json
import re

import requests

from . import chart_registry, processing
from ..config import settings
from .plan_schema import parse_plan

_LOCAL_HOSTS = {"127.0.0.1", "localhost", "::1", "[::1]"}

# Session that ignores system proxy settings — LLM traffic must go direct to
# localhost (a system HTTP proxy can hijack or time out local calls).
_session = requests.Session()
_session.trust_env = False


class LLMError(RuntimeError):
    pass


def ensure_local_endpoint(url: str) -> None:
    """Fail closed if a non-local LLM endpoint is configured."""
    host = url.split("//")[-1].split("/")[0].split(":")[0]
    if host not in _LOCAL_HOSTS:
        raise LLMError(
            f"Refusing non-local LLM endpoint '{url}'. BankViz only allows localhost for privacy."
        )


def ollama_reachable(url: str | None = None, timeout: float = 2.0) -> bool:
    try:
        r = _session.get(f"{url or settings.OLLAMA_URL}/api/tags", timeout=timeout)
        return r.status_code == 200
    except requests.RequestException:
        return False


def build_prompt(meta: dict) -> list[dict]:
    """Messages for the plan-generation chat. Metadata only — no row data."""
    system = (
        "You are a data-visualisation planner for retail banking datasets. "
        "You respond with ONLY a JSON object, no prose. "
        'Format: {"charts": [{"chart_type": str, "title": str, "rationale": str, '
        '"x": str|null, "y": str|null, "group": str|null, '
        '"agg": "sum"|"mean"|"count"|"min"|"max"|"median", "bins": int|null, "filter": str|null}]}'
    )
    user = f"""You are given METADATA ONLY of a retail-banking dataset (never the raw rows).

DATASET METADATA (data_A):
{json.dumps(meta, ensure_ascii=False, indent=1)}

AVAILABLE CHART TYPES (data_B) — use only these ids:
{json.dumps(chart_registry.library_descriptions(), ensure_ascii=False, indent=1)}

AVAILABLE PROCESSING FUNCTIONS (data_C) — the system applies them for you:
{json.dumps(processing.FUNCTION_DESCRIPTIONS, ensure_ascii=False, indent=1)}

BANKING DOMAIN RULES:
- Produce 3 to 8 charts prioritising: customer segmentation, transaction behaviour, churn/retention, risk exposure, product adoption.
- NEVER use identifier columns (e.g. customer id) on any axis.
- Prefer aggregated comparisons (bar/box/grouped_bar) over raw scatter unless the relationship is genuinely interesting.
- Pie charts only for categories with few values.
- Use ONLY columns that exist in the metadata. Use "agg" for numeric Y.
- Each chart needs a short business "rationale" (why it matters to a bank analyst).

Return ONLY the JSON object."""
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


def _extract_json(text: str):
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.DOTALL)
    return json.loads(text)


def call_llm(meta: dict, timeout: float | None = None) -> list:
    """Call local Ollama and return parsed ChartSpec list (may be empty)."""
    ensure_local_endpoint(settings.OLLAMA_URL)
    payload = {
        "model": settings.OLLAMA_MODEL,
        "messages": build_prompt(meta),
        "stream": False,
        "format": "json",
        # num_ctx 4096 is plenty for metadata-only prompts and keeps the KV
        # cache small on CPU-only machines with limited free RAM.
        "options": {"temperature": 0.2, "num_ctx": 4096},
    }
    last_error = None
    for _ in range(2):  # one repair/retry round
        try:
            resp = _session.post(
                f"{settings.OLLAMA_URL}/api/chat",
                json=payload,
                timeout=timeout or settings.OLLAMA_TIMEOUT,
            )
            resp.raise_for_status()
            content = resp.json()["message"]["content"]
            return parse_plan(_extract_json(content))
        except (requests.RequestException, KeyError, json.JSONDecodeError) as exc:
            last_error = exc
    raise LLMError(f"LLM plan generation failed after retry: {last_error}")
