# User Stories & Use Cases — BankViz (Local Auto-Visualisation Tool for Retail-Bank Datasets)

Project: MSc IT+ Development Project
Goal: A fully local tool that ingests retail-banking CSV/Excel datasets, extracts metadata, and uses a locally hosted LLM to generate and execute visualization plans, plus a manual chart-customisation mode. No raw data ever leaves the user's machine.

Actors:

- **Analyst** (primary user): a retail-bank business analyst or student exploring customer/transaction datasets. Non-technical; no coding, no login.
- **System** (BankViz backend): FastAPI service containing data_A (metadata extractor), data_B (chart library), data_C (processing functions), plan executor, domain filter.
- **LLM** (Ollama, local): open-source model (e.g. Qwen2.5-7B-Instruct) that receives metadata + library descriptions and returns a structured visualization plan (JSON), never raw data.

---

## Epic 1 — Dataset Ingestion & Metadata (data_A)

### US-1.1 Upload a dataset
> **As an** Analyst, **I want to** upload a CSV or Excel file of bank customers/transactions, **so that** I can start exploring it without any technical setup.

- **Acceptance criteria**
  - AC1: Accepts `.csv`, `.xlsx`, `.xls` up to a configurable size limit (default 100 MB).
  - AC2: Invalid/empty files are rejected with a clear, human-readable error.
  - AC3: The file is stored only in local memory/temp storage; no outbound network calls occur.
  - AC4: A dataset session ID is returned and used for all subsequent operations.

### US-1.2 Extract dataset metadata
> **As an** Analyst, **I want to** see a structured summary of my dataset (columns, types, ranges, missing values), **so that** I understand what I am working with before charting.

- **Acceptance criteria**
  - AC1: For every column the system reports: name, inferred data type (numeric / categorical / datetime / boolean / identifier), min–max or top categories, missing-value count and %, unique-value count.
  - AC2: Numeric columns include count/mean/std/quartiles.
  - AC3: Metadata is returned as JSON and displayed on the dataset overview page.
  - AC4: Column names are sanitised and never sent anywhere except the local LLM.

### UC-1: Ingest & Profile Dataset
- **Actor:** Analyst
- **Precondition:** BankViz is running locally; user has a CSV/Excel file.
- **Main flow:**
  1. Analyst opens the web UI and uploads a file.
  2. System validates format and loads the file with pandas.
  3. System extracts data_A metadata and creates a session.
  4. System returns metadata; UI shows the dataset overview (schema, quality stats).
- **Extensions:**
  - 2a. Unsupported format → error message, flow ends.
  - 3a. Column of mixed types → typed as "mixed" with warning.
- **Postcondition:** Dataset held in memory under session ID; metadata available.

---

## Epic 2 — Built-in Libraries (data_B charts, data_C processing)

### US-2.1 Pre-coded chart components
> **As an** Analyst, **I want to** rely on a library of ready-made chart components (bar, box, scatter, pie, heatmap, histogram, line), **so that** every chart is correctly rendered without me configuring anything.

- **Acceptance criteria**
  - AC1: Each chart type in data_B exposes: id, name, description, required input signature (e.g. 1 categorical + 1 numeric), and usage guidance.
  - AC2: Chart builders are pure functions: (DataFrame + spec) → chart data JSON (ECharts-compatible).
  - AC3: Unknown or malformed chart specs fail validation before rendering.

### US-2.2 Reusable financial processing functions
> **As an** Analyst, **I want** grouping, summation, mean, counting and binning operations applied automatically behind charts, **so that** charts reflect proper financial aggregations rather than raw rows.

- **Acceptance criteria**
  - AC1: data_C exposes: group-aggregate (sum/mean/count/min/max), value binning (equal-width & quantile), top-N filtering, correlation matrix.
  - AC2: Aggregations are used whenever a chart's cardinality would exceed a readable threshold (e.g. > 30 categories).
  - AC3: Every chart plan references the processing functions it uses, making the pipeline auditable.

---

## Epic 3 — LLM-Driven Automatic Visualisation

### US-3.1 Generate a visualisation plan
> **As an** Analyst, **I want to** click "Auto-generate charts" and receive a set of relevant charts, **so that** I get insight in seconds without choosing chart types or axes.

- **Acceptance criteria**
  - AC1: System sends the local LLM: dataset metadata (data_A), chart library descriptions (data_B), processing function descriptions (data_C), and a banking-domain instruction — never raw row data.
  - AC2: LLM responds with a structured JSON plan: a list of chart specs `{chart_type, title, rationale, x, y, group, agg, filter, bins}`.
  - AC3: The plan is validated (schema + column existence + chart/input compatibility); invalid specs are dropped or repaired by fallback rules.
  - AC4: The plan is displayed to the user with each chart's rationale before/alongside rendering.

### US-3.2 Domain-aware filtering
> **As an** Analyst, **I want** the tool to prioritise banking-relevant charts and suppress meaningless ones, **so that** I don't waste time on noise.

- **Acceptance criteria**
  - AC1: Charts targeting business themes (customer segmentation, transaction behaviour, churn, risk exposure, product adoption) are ranked first.
  - AC2: Hard rules suppress meaningless mappings, e.g. unique-ID column on an axis, categorical pairs with cardinality > 30, single-column charts of IDs.
  - AC3: Filtering happens in two layers: prompt guidance (soft) + deterministic rule engine (hard). The rule engine runs even if the LLM output violates guidance.

### US-3.3 Execute the plan
> **As an** Analyst, **I want** the approved plan rendered into actual charts, **so that** I can see the results immediately.

- **Acceptance criteria**
  - AC1: The backend executes each validated spec via data_B/data_C and returns ECharts-ready JSON.
  - AC2: If one chart fails, remaining charts still render; the failure is reported per chart.
  - AC3: Charts are rendered locally in the browser; nothing is uploaded.

### UC-2: Automatic Visual Exploration
- **Actor:** Analyst, System, LLM (local)
- **Precondition:** A dataset session exists (UC-1); Ollama is running.
- **Main flow:**
  1. Analyst clicks "Auto-generate".
  2. System builds the LLM prompt from data_A + data_B + data_C + domain instructions.
  3. LLM returns a candidate plan (JSON).
  4. System validates and filters the plan (schema check → column check → domain rule engine).
  5. System executes the surviving specs and returns chart data.
  6. UI renders charts with titles, rationales and the processing functions used.
- **Extensions:**
  - 2a. Ollama unreachable → fallback statistical recommender produces a default plan; UI notes degraded mode.
  - 3a. Invalid JSON → one automatic repair/retry round; on second failure, fallback recommender.
  - 4a. All specs filtered out → UI explains why and suggests manual mode.
- **Postcondition:** Chart dashboard displayed; plan stored in session history.

---

## Epic 4 — Manual Custom Visualisation

### US-4.1 Build a chart manually
> **As an** Analyst, **I want to** pick chart type, X, Y, grouping and aggregation myself, **so that** I can answer my own specific questions beyond the auto plan.

- **Acceptance criteria**
  - AC1: UI offers dropdowns populated from data_A (columns, types) and data_B (chart types).
  - AC2: Invalid combinations are prevented or rejected with explanation (e.g. pie chart with > 8 slices suggests bar).
  - AC3: Generated chart uses the same data_B/data_C pipeline as the automatic mode (one execution engine).
  - AC4: Charts can be exported as PNG.

### UC-3: Manual Chart Creation
- **Actor:** Analyst
- **Precondition:** A dataset session exists.
- **Main flow:**
  1. Analyst opens Manual mode.
  2. Analyst selects chart type and variables; UI validates compatibility.
  3. Analyst clicks Generate; system executes spec through the same pipeline.
  4. Chart is displayed and can be exported.
- **Extensions:** 2a. Incompatible selection → inline guidance message.
- **Postcondition:** Chart added to session history.

---

## Epic 5 — Privacy & Local Operation

### US-5.1 Guaranteed-local processing
> **As an** Analyst, **I want** assurance that no customer data leaves my machine, **so that** the tool is compliant with banking data-privacy requirements.

- **Acceptance criteria**
  - AC1: All computation (pandas, LLM inference, rendering) runs on localhost; the app makes zero external network requests at runtime.
  - AC2: The LLM prompt contains metadata + schema only — never row-level values beyond aggregate statistics already shown to the user.
  - AC3: No user login, no accounts, no telemetry.
  - AC4: A startup self-check confirms the Ollama endpoint is local and fails closed if a remote endpoint is configured.

### UC-4: Privacy-Preserving Session
- **Actor:** Analyst, System
- **Main flow:**
  1. Analyst starts BankViz (`run_local.bat` / two commands).
  2. System verifies local LLM endpoint (localhost only) and starts UI.
  3. All UC-1..UC-3 flows execute without any outbound request.
- **Postcondition:** Session data lives in memory; cleared on shutdown.

---

## Traceability Matrix (stories → objectives)

| Story | Mandatory objective covered |
|-------|------------------------------|
| US-1.1 / US-1.2 | Ingest CSV/Excel + extract data_A metadata |
| US-2.1 / US-2.2 | data_B chart library + data_C processing functions |
| US-3.1 / US-3.3 | LLM outputs plans (not images); system parses & invokes pre-implemented functions |
| US-3.2 | Banking domain awareness, suppress meaningless charts |
| US-4.1 | Manual visualisation mode |
| US-5.1 | Data stays local, no network, no login |
