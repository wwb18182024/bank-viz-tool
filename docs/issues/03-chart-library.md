---
title: "US-2.1 Chart component library (data_B)"
labels: epic:libraries, backend, milestone-1
---
**Story:** As an Analyst, I want a library of ready-made chart components, so that every chart renders correctly without configuration.

**Tasks**
- [ ] Registry with: bar, grouped bar, pie, histogram, box plot, scatter, line, heatmap (correlation), stacked bar
- [ ] Each entry: id, name, description, required input signature, usage guidance text (for LLM prompt)
- [ ] Pure builder functions: (DataFrame, spec) → ECharts-compatible JSON
- [ ] Spec validation (required fields, column existence)
- [ ] Unit tests per chart type

**Reference:** US-2.1
