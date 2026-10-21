---
title: "US-4.1 Manual chart builder endpoint"
labels: epic:manual, backend, milestone-2
---
**Story:** As an Analyst, I want to pick chart type, X, Y, grouping and aggregation myself.

**Tasks**
- [ ] `POST /api/manual/{dataset_id}/chart` using the same ChartSpec schema and execution engine as auto mode
- [ ] Compatibility pre-checks with explanatory errors (e.g. pie with > 8 categories → suggest bar)
- [ ] PNG export support (server-side matplotlib render of the same spec, or client-side canvas export — decide in review)
- [ ] Unit tests

**Reference:** US-4.1, UC-3
