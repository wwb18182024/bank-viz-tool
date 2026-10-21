---
title: "US-3.2 Domain-aware plan validation & filtering (two-layer rule engine)"
labels: epic:autoviz, backend, milestone-2
---
**Story:** As an Analyst, I want banking-relevant charts prioritised and meaningless ones suppressed.

**Tasks**
- [ ] Hard rules: reject ID-like columns on axes, cardinality > 30 categorical pairs, duplicate specs, incompatible chart/column types
- [ ] Ranking: boost specs whose rationale matches banking themes (segmentation, transaction behaviour, churn, risk, product adoption)
- [ ] Rule engine runs regardless of LLM compliance (LLM guidance is only the soft layer)
- [ ] Endpoint `POST /api/autoviz/{dataset_id}/execute`: validate → filter → execute via data_B/data_C → per-chart success/error payloads
- [ ] Unit tests for each rule

**Reference:** US-3.2, US-3.3, UC-2
