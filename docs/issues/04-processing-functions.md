---
title: "US-2.2 Financial data-processing functions (data_C)"
labels: epic:libraries, backend, milestone-1
---
**Story:** As an Analyst, I want grouping/sum/mean/count/binning applied behind charts, so that charts show proper financial aggregations.

**Tasks**
- [ ] `core/processing.py`: group-aggregate (sum/mean/count/min/max), equal-width & quantile binning, top-N filter, correlation matrix
- [ ] Auto-aggregation when categorical cardinality > 30
- [ ] Each executed chart records which processing functions were applied (auditability for thesis)
- [ ] Unit tests

**Reference:** US-2.2
