from app.core.metadata import extract_metadata
from app.core.fallback_recommender import recommend_plan
from app.core.plan_validator import filter_plan


def test_fallback_produces_valid_plan(bank_df):
    meta = extract_metadata(bank_df)
    specs = recommend_plan(meta)
    assert 3 <= len(specs) <= 8
    accepted, rejected = filter_plan(specs, meta)
    assert len(accepted) >= 4
    assert all(r["reason"] for r in rejected)


def test_fallback_avoids_identifiers(bank_df):
    meta = extract_metadata(bank_df)
    for spec in recommend_plan(meta):
        for col in (spec.x, spec.y, spec.group):
            assert col != "CustomerID"
