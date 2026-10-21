import pandas as pd
import pytest

from app.core.processing import apply_filter, bin_values, group_aggregate, top_n


def test_group_aggregate_sum(bank_df):
    out = group_aggregate(bank_df, "Geography", "Balance", "sum")
    assert set(out.columns) == {"Geography", "sum_Balance"}
    assert out["sum_Balance"].sum() == pytest.approx(bank_df["Balance"].sum())


def test_group_aggregate_count(bank_df):
    out = group_aggregate(bank_df, "Gender", None, "count")
    assert out["count"].sum() == len(bank_df)


def test_bin_values_quantile(bank_df):
    binned = bin_values(bank_df["Balance"], bins=4, strategy="quantile")
    assert binned.notna().sum() > 0


def test_top_n_merges_rare_categories():
    df = pd.DataFrame({"cat": list("abcdef") * 10})
    out = top_n(df, "cat", n=3)
    assert out["cat"].nunique() == 4  # 3 kept + Other


def test_apply_filter_numeric(bank_df):
    out = apply_filter(bank_df, "Balance>10000")
    assert (out["Balance"] > 10000).all()


def test_apply_filter_categorical(bank_df):
    out = apply_filter(bank_df, "Geography=France")
    assert (out["Geography"] == "France").all()


def test_apply_filter_invalid_column(bank_df):
    with pytest.raises(ValueError):
        apply_filter(bank_df, "NoSuchColumn=1")
