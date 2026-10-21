"""End-to-end API tests with TestClient (LLM mocked / fallback used)."""
import io

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _csv_bytes(bank_df) -> bytes:
    return bank_df.to_csv(index=False).encode()


def test_upload_and_metadata(bank_df):
    resp = client.post(
        "/api/datasets/upload",
        files={"file": ("bank.csv", io.BytesIO(_csv_bytes(bank_df)), "text/csv")},
    )
    assert resp.status_code == 200
    dataset_id = resp.json()["dataset_id"]

    meta = client.get(f"/api/datasets/{dataset_id}/metadata").json()
    assert meta["n_rows"] == 300
    assert any(c["name"] == "Churn" for c in meta["columns"])

    assert client.delete(f"/api/datasets/{dataset_id}").status_code == 200


def test_upload_rejects_bad_extension():
    resp = client.post(
        "/api/datasets/upload",
        files={"file": ("malware.exe", io.BytesIO(b"MZ..."), "application/octet-stream")},
    )
    assert resp.status_code == 400


def test_manual_chart_endpoint(bank_df):
    upload = client.post(
        "/api/datasets/upload",
        files={"file": ("bank.csv", io.BytesIO(_csv_bytes(bank_df)), "text/csv")},
    ).json()
    dataset_id = upload["dataset_id"]

    options = client.get(f"/api/manual/{dataset_id}/options").json()
    assert any(c["id"] == "bar" for c in options["chart_types"])

    resp = client.post(
        f"/api/manual/{dataset_id}/chart",
        json={"chart_type": "bar", "title": "Mean balance by geography", "x": "Geography", "y": "Balance", "agg": "mean"},
    )
    assert resp.status_code == 200
    assert resp.json()["ok"] is True

    # Invalid spec → 422 with reason
    bad = client.post(
        f"/api/manual/{dataset_id}/chart",
        json={"chart_type": "scatter", "title": "bad", "x": "Geography", "y": "Balance"},
    )
    assert bad.status_code == 422


def test_autoviz_execute_fallback(bank_df, monkeypatch):
    """When Ollama is unreachable, the pipeline must still return charts (degraded mode)."""
    from app.core import llm_client

    def _fail(meta, timeout=120.0):
        raise llm_client.LLMError("simulated offline")

    monkeypatch.setattr(llm_client, "call_llm", _fail)

    upload = client.post(
        "/api/datasets/upload",
        files={"file": ("bank.csv", io.BytesIO(_csv_bytes(bank_df)), "text/csv")},
    ).json()
    dataset_id = upload["dataset_id"]

    plan = client.post(f"/api/autoviz/{dataset_id}/plan").json()
    assert plan["source"] == "fallback"
    assert len(plan["plan"]) >= 3

    result = client.post(f"/api/autoviz/{dataset_id}/execute").json()
    ok_charts = [c for c in result["charts"] if c["ok"]]
    assert len(ok_charts) >= 3


def test_privacy_remote_endpoint_refused():
    import requests
    from app.config import settings
    from app.core.llm_client import LLMError, ensure_local_endpoint

    try:
        ensure_local_endpoint("http://api.openai.com/v1")
        raise AssertionError("Remote endpoint was not refused")
    except LLMError:
        pass
    assert settings.OLLAMA_URL.startswith(("http://127.0.0.1", "http://localhost", "http://[::1]"))
