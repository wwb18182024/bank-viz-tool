import pytest

from app.core.metadata import extract_metadata, infer_semantic_type


def test_identifier_detection(bank_df):
    assert infer_semantic_type("CustomerID", bank_df["CustomerID"]) == "identifier"


def test_numeric_and_categorical(bank_df):
    assert infer_semantic_type("Balance", bank_df["Balance"]) == "numeric"
    assert infer_semantic_type("Geography", bank_df["Geography"]) == "categorical"
    assert infer_semantic_type("Churn", bank_df["Churn"]) == "numeric"


def test_metadata_structure(bank_df):
    meta = extract_metadata(bank_df)
    assert meta["n_rows"] == 300
    assert meta["n_columns"] == bank_df.shape[1]
    cols = {c["name"]: c for c in meta["columns"]}
    assert cols["Balance"]["min"] is not None
    assert cols["Balance"]["mean"] is not None
    assert cols["Geography"]["top_values"][0]["count"] > 0
    assert cols["CustomerID"]["unique"] == 300


def test_missing_values(bank_df):
    df = bank_df.copy()
    df.loc[df.index[:10], "Balance"] = None
    meta = extract_metadata(df)
    col = next(c for c in meta["columns"] if c["name"] == "Balance")
    assert col["missing"] == 10
    assert col["missing_pct"] == pytest.approx(10 / 300 * 100, abs=0.01)
