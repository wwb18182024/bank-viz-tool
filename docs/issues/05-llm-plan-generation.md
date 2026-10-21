---
title: "US-3.1 Local LLM client + visualisation plan generation"
labels: epic:autoviz, backend, llm, milestone-2
---
**Story:** As an Analyst, I want to click "Auto-generate charts" and get a set of relevant charts.

**Tasks**
- [ ] `core/llm_client.py`: Ollama client (localhost default, e.g. Qwen2.5-7B-Instruct), JSON-mode prompt
- [ ] Prompt builder: data_A + data_B descriptions + data_C descriptions + banking-domain instructions (metadata only, no row data)
- [ ] Pydantic `VisPlan` / `ChartSpec` schema: chart_type, title, rationale, x, y, group, agg, bins, filter
- [ ] `POST /api/autoviz/{dataset_id}/plan` returns the parsed plan
- [ ] One repair/retry round on invalid JSON; then fallback to statistical recommender (degraded mode flag)
- [ ] Unit tests with a mocked LLM

**Reference:** US-3.1, UC-2
