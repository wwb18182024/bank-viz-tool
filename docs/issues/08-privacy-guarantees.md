---
title: "US-5.1 Privacy self-check & local-only guarantees"
labels: epic:privacy, backend, milestone-2
---
**Story:** As an Analyst, I want assurance that no data leaves my machine.

**Tasks**
- [ ] Startup check: configured LLM endpoint must be localhost/127.0.0.1; refuse remote endpoints (fail closed)
- [ ] Prompt audit: assert prompt builder input contains metadata only (test with sentinel row values)
- [ ] `GET /api/health` reports local-mode status
- [ ] No telemetry, no login anywhere in codebase; README documents the guarantee

**Reference:** US-5.1, UC-4
