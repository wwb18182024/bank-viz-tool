"""Dataset ingestion & metadata endpoints (data_A)."""
from __future__ import annotations

import io

import pandas as pd
from fastapi import APIRouter, File, HTTPException, UploadFile

from ..config import settings
from ..core.metadata import extract_metadata
from ..core.session_store import store

router = APIRouter(prefix="/api/datasets", tags=["datasets"])


def _load_dataframe(filename: str, content: bytes) -> pd.DataFrame:
    suffix = "." + filename.rsplit(".", 1)[-1].lower()
    if suffix == ".csv":
        return pd.read_csv(io.BytesIO(content))
    try:
        return pd.read_excel(io.BytesIO(content))
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=f"Cannot read Excel file: {exc}")


@router.post("/upload")
async def upload_dataset(file: UploadFile = File(...)):
    filename = file.filename or ""
    if "." not in filename or ("." + filename.rsplit(".", 1)[-1].lower()) not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Only .csv, .xlsx, .xls files are supported")
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")
    if len(content) > settings.MAX_UPLOAD_MB * 1024 * 1024:
        raise HTTPException(status_code=413, detail=f"File exceeds {settings.MAX_UPLOAD_MB} MB limit")
    try:
        df = _load_dataframe(filename, content)
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=f"Cannot parse file: {exc}")
    if df.empty:
        raise HTTPException(status_code=400, detail="The dataset contains no rows")
    df.columns = [str(c).strip() for c in df.columns]
    session = store.create(df, filename)
    return {
        "dataset_id": session.dataset_id,
        "filename": session.filename,
        "n_rows": int(len(df)),
        "n_columns": int(len(df.columns)),
        "columns": list(df.columns),
    }


@router.get("/{dataset_id}/metadata")
def get_metadata(dataset_id: str):
    session = store.get(dataset_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Dataset session not found (it may have expired after a server restart)")
    return {"dataset_id": dataset_id, "filename": session.filename, **extract_metadata(session.df)}


@router.delete("/{dataset_id}")
def delete_dataset(dataset_id: str):
    if not store.delete(dataset_id):
        raise HTTPException(status_code=404, detail="Dataset session not found")
    return {"deleted": dataset_id}
