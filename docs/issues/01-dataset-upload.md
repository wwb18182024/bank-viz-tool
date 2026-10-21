---
title: "US-1.1 Dataset upload endpoint (CSV/Excel) with session management"
labels: epic:ingestion, backend, milestone-1
---
**Story:** As an Analyst, I want to upload a CSV or Excel file, so that I can start exploring it without technical setup.

**Tasks**
- [ ] FastAPI endpoint `POST /api/datasets/upload` accepting `.csv/.xlsx/.xls` (size limit configurable, default 100 MB)
- [ ] Reject invalid/empty files with human-readable errors
- [ ] In-memory session store: dataset id → DataFrame (no disk persistence of user data)
- [ ] Unit tests: valid csv, valid xlsx, empty file, wrong extension

**Reference:** docs/user-stories-and-use-cases.md → US-1.1, UC-1
