"""Fix multi-line table cells in the tracker PPT (newlines must be \r)."""
import json
import subprocess
import sys

EDSDK = r"C:\Users\Administrator\.workbuddy\plugins\cache\workbuddy-builtin\workbuddy-pptx\5.8.3-wb.41334564.gdb0e9b51.h4da087921e4a\skills\workbuddy-pptx\scripts\edsdk.py"
FILE_ID = "41711538-FB89-4036-AA9A-607CD0D11B5A"

CELLS = [
    # (page_index, shape_id, text)
    (14, "000112", "- User stories and use cases documented (5 epics, 4 use cases)\r- 13 development tasks created on GitLab\r- Backend implemented: metadata extraction (data_A), chart library (data_B), financial processing functions (data_C), LLM plan generation with schema validation and two-layer domain filtering\r- React frontend: upload, auto-viz dashboard, manual chart builder\r- 34 backend tests passing"),
    (14, "000115", "- 26 Oct supervisor meeting: demo end-to-end pipeline and review code\r- Verify full pipeline with local LLM (qwen2.5)\r- Begin evaluation planning for chart business relevance"),
    (14, "000114", "- CPU-only machine: 7B model too slow (memory-bound) - using qwen2.5:3b (~30 s/plan), acceptable for JSON planning\r- LLM occasionally hallucinates column names - caught by plan validator (evidence for two-layer design)"),
    (16, "000120", "26 Oct supervisor meeting:\r- Code review of complete front-end + back-end\r- Demo of automatic and manual visualisation modes\r- Agree next steps: evaluation design and dissertation plan"),
    (16, "00011f", "- Full pipeline verified end-to-end with local LLM (qwen2.5:3b): plan generated, validated, 4/4 charts rendered\r- LLM client hardened for CPU-only machines (proxy bypass, context sizing, timeouts)\r- Architecture diagram added to tracker"),
    (16, "000122", "- Polish UI and chart export\r- Define evaluation rubric for chart business relevance; run on 2-3 open bank datasets\r- Draft dissertation chapters (architecture, implementation)\r- Record demonstration video"),
    (16, "000121", "- Demo readiness: Ollama service must be running; first LLM call has cold-start delay (warm up before demo)\r- Heatmap readability with many numeric columns - mitigated by metadata-driven column selection"),
    (13, "00010a", "- Agreed project topic and aims\r- Reviewed similar tools (cloud auto-visualisation, BI) and identified the privacy + domain-awareness gap\r- Selected tech stack: Python/FastAPI, React, Ollama (local open-source LLM)\r- Set up GitLab repository and local dev environment"),
    (13, "00010d", "- Write user stories and use cases\r- Create development tasks on GitLab\r- Implement dataset upload + metadata extraction (data_A)\r- Deploy local LLM (Ollama) and verify JSON plan output"),
    (13, "00010c", "- LLM must output strictly valid JSON plans - mitigation: schema validation + retry + statistical fallback\r- No GPU on dev machine - may limit usable local model size\r- Keeping charts banking-relevant, not just statistically valid"),
    (13, "00010b", "Initial supervisor meeting:\r- Confirm topic: local LLM-driven auto-visualisation tool for retail-bank datasets\r- Agree mandatory objectives and success criteria\r- Agree 12-week working plan"),
]

for page, shape, text in CELLS:
    payload = {
        "file_id": FILE_ID,
        "page_index": page,
        "shape_id": shape,
        "row": 1,
        "col": 0,
        "text": text,
    }
    result = subprocess.run(
        [sys.executable, EDSDK, "call", "slide_set_cell_text", "--json", json.dumps(payload)],
        capture_output=True, text=True,
    )
    ok = '"ok":true' in result.stdout.replace(" ", "")
    print(("OK  " if ok else "FAIL"), page, shape, result.stdout.strip()[:80], result.stderr.strip()[:80])
