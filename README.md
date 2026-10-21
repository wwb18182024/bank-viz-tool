# BankViz — Local LLM-Powered Visual Exploration for Retail-Bank Datasets

A fully local tool that ingests retail-banking CSV/Excel datasets, extracts structured
metadata, and uses a **locally hosted open-source LLM** to generate and execute data
visualisation plans — plus a manual chart-builder mode. **No raw data ever leaves the
user's machine.**

MSc IT+ Development Project.

## Architecture

```
┌─────────────────────────┐        ┌──────────────────────────────────────┐
│  React frontend (Vite)  │  HTTP  │  FastAPI backend (localhost:8000)    │
│  - Upload & metadata UI │ ─────► │  - data_A: metadata extractor        │
│  - Auto-viz dashboard   │        │  - data_B: chart library (12 types)  │
│  - Manual builder       │        │  - data_C: financial processing fns  │
│  - ECharts rendering    │        │  - Plan schema + validator + filter  │
└─────────────────────────┘        │  - Executor → chart JSON             │
                                   └──────────────┬───────────────────────┘
                                                  │ metadata only (never rows)
                                   ┌──────────────▼───────────────────────┐
                                   │  Ollama (localhost:11434)            │
                                   │  Qwen2.5-7B-Instruct (or similar)    │
                                   └──────────────────────────────────────┘
```

**Pipeline (auto mode):** upload → metadata (data_A) → prompt = metadata + data_B +
data_C descriptions + banking-domain rules → local LLM returns a JSON **visualisation
plan** (not images) → schema validation → deterministic domain-rule filtering (ranking
+ suppression of meaningless charts) → plan executor invokes pre-coded chart builders →
ECharts JSON rendered in the browser.

If the LLM is offline or returns nothing valid, a **statistical fallback recommender**
keeps the tool usable (degraded mode, clearly indicated in the UI).

## Privacy guarantees

- All computation (pandas profiling, LLM inference, chart rendering) runs on localhost.
- The backend **refuses remote LLM endpoints** at startup (fail closed).
- The LLM prompt contains **metadata only** — never row-level data.
- No login, no accounts, no telemetry, no outbound requests at runtime.

## Quick start

Prerequisites: Python 3.12+, Node.js 18+, and [Ollama](https://ollama.com) (optional but recommended).

1. **Local LLM** (recommended):
   ```bat
   ollama serve
   ollama pull qwen2.5:7b-instruct-q4_K_M
   ```

2. **Backend**:
   ```bat
   cd backend
   python -m venv .venv            (once; or use the prebuilt E:\bank-viz-tool\.venv)
   .venv\Scripts\pip install -r requirements.txt
   .venv\Scripts\python -m uvicorn app.main:app --port 8000
   ```

3. **Frontend** (second terminal):
   ```bat
   cd frontend
   npm install
   npm run dev
   ```

4. Open **http://localhost:5173**, upload `data/sample_bank_customers.csv` (2,000 synthetic
   customers) or any bank CSV/Excel, then use *Auto-visualise* or the *Manual builder*.

Or simply run **`run_local.bat`** (starts both servers).

## Tests

```bat
cd backend
.venv\Scripts\python -m pytest tests\ -q     # 34 tests: metadata, processing, charts, validation, API e2e
```

## Project layout

```
backend/app/core/       data_A metadata.py · data_B chart_registry.py · data_C processing.py
                        plan_schema.py · plan_validator.py (domain rules) · llm_client.py
                        fallback_recommender.py · executor.py · session_store.py
backend/app/api/        REST endpoints (datasets / autoviz / manual / health)
backend/tests/          pytest suite
frontend/src/           React app (Upload / AutoViz / Manual pages, ECharts cards)
docs/                   user-stories-and-use-cases.md · issues/ (13 GitLab-ready issue files)
scripts/create_issues.py  one-command GitLab issue import (see file header)
data/                   synthetic sample dataset + generator script
```

## Configuration (environment variables)

| Variable | Default | Purpose |
|----------|---------|---------|
| `OLLAMA_URL` | `http://127.0.0.1:11434` | Local LLM endpoint (must be local) |
| `OLLAMA_MODEL` | `qwen2.5:7b-instruct-q4_K_M` | Model tag |
| `MAX_UPLOAD_MB` | `100` | Upload size limit |

## Domain-aware filtering (two layers)

1. **Soft** — banking-domain instructions in the LLM prompt (segmentation, transaction
   behaviour, churn, risk, product adoption first).
2. **Hard** — deterministic rules that always run: identifier columns rejected on any
   axis, high-cardinality pies/counts suppressed, chart/column type compatibility
   enforced, duplicates removed, banking-themed charts ranked first.
