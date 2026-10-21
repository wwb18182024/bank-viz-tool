---
title: "US-1.2 Metadata extraction engine (data_A)"
labels: epic:ingestion, backend, milestone-1
---
**Story:** As an Analyst, I want a structured profile of my dataset, so that I understand what I am working with.

**Tasks**
- [ ] `core/metadata.py`: per-column name, inferred type (numeric/categorical/datetime/boolean/identifier/mixed)
- [ ] Min–max for numeric, top-k categories for categorical, datetime range
- [ ] Missing count + %, unique count, numeric describe() stats
- [ ] Endpoint `GET /api/datasets/{id}/metadata`
- [ ] Unit tests on a synthetic bank dataset

**Reference:** US-1.2, UC-1
