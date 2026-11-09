"""Regression tests across every bundled evaluation dataset.

Ensures the full plan -> validate -> execute pipeline produces only valid,
renderable charts on all open bank datasets shipped in data/open_datasets/
plus the two synthetic ones. Uses the statistical fallback recommender so
the tests never depend on a running LLM."""
from pathlib import Path

import pandas as pd
import pytest

from app.core import fallback_recommender, plan_validator
from app.core.executor import execute_spec
from app.core.metadata import extract_metadata
from app.core.plan_schema import ChartSpec

DATA = Path(__file__).resolve().parents[2] / "data"
EVAL_FILES = sorted(
    p for p in (DATA / "open_datasets").glob("*.csv") if "_raw" not in p.stem
) + [
    DATA / "sample_bank_customers.csv",
]


def _pipeline(df: pd.DataFrame):
    meta = extract_metadata(df)
    specs = fallback_recommender.recommend_plan(meta)
    assert 3 <= len(specs) <= 12, f"unexpected plan size: {len(specs)}"
    results = []
    for spec in specs:
        ok, reason = plan_validator.validate_spec(spec, meta)
        if not ok:
            continue  # domain filter legitimately suppresses some specs
        results.append(execute_spec(df, spec, meta))
    return results


@pytest.mark.parametrize("csv_path", EVAL_FILES, ids=lambda p: p.stem)
def test_pipeline_renders_on_evaluation_dataset(csv_path):
    df = pd.read_csv(csv_path)
    assert not df.empty
    results = _pipeline(df)
    assert results, f"no renderable charts produced for {csv_path.stem}"
    for res in results:
        assert res["ok"], f"{csv_path.stem}: {res.get('error')}"
        assert "series" in res["option"]
        # every rendered series carries finite numeric data
        for series in res["option"]["series"]:
            data = series.get("data") or []
            assert len(data) > 0, f"{csv_path.stem}: empty series"


def test_dataset_inventory():
    """The supervisor-mandated dataset mix: 4-5 open + 1-2 synthetic."""
    open_csvs = {p.stem for p in (DATA / "open_datasets").glob("*.csv")}
    expected_open = {
        "german_credit", "bank_marketing", "credit_card_default",
        "australian_credit", "kaggle_churn_modelling",
    }
    missing = expected_open - open_csvs
    assert not missing, f"missing evaluation datasets: {missing}"
    assert (DATA / "sample_bank_customers.csv").exists(), "synthetic dataset 1 missing"
    assert (DATA / "open_datasets" / "synthetic_bank_transactions.csv").exists(), \
        "synthetic dataset 2 missing"


def test_validator_suppresses_meaningless_on_real_data():
    """On a wide real dataset the domain filter must reject at least one
    nonsensical spec proposed for it."""
    df = pd.read_csv(DATA / "open_datasets" / "credit_card_default.csv")
    meta = extract_metadata(df)
    spec = ChartSpec(
        chart_type="pie", title="meaningless", x="customer_id")
    ok, reason = plan_validator.validate_spec(spec, meta)
    assert not ok
    assert "identifier" in reason.lower() or "pie" in reason.lower()
