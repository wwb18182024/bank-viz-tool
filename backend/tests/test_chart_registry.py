from app.core.plan_schema import ChartSpec
from app.core import chart_registry
from app.core.executor import execute_spec


def _meta(bank_df):
    from app.core.metadata import extract_metadata
    return extract_metadata(bank_df)


def test_registry_signatures():
    assert "bar" in chart_registry.REGISTRY
    assert len(chart_registry.REGISTRY) >= 8
    for entry in chart_registry.library_descriptions():
        assert {"id", "name", "usage", "input"} <= set(entry)


def test_bar_builder(bank_df):
    spec = ChartSpec(chart_type="bar", title="Avg balance by geography", x="Geography", y="Balance", agg="mean")
    result = execute_spec(bank_df, spec, _meta(bank_df))
    assert result["ok"]
    assert result["option"]["xAxis"]["data"]
    assert "group_aggregate" in result["functions_used"][0]


def test_pie_builder(bank_df):
    spec = ChartSpec(chart_type="pie", title="Churn share", x="Churn", agg="count")
    result = execute_spec(bank_df, spec, _meta(bank_df))
    assert result["ok"]
    assert result["option"]["series"][0]["type"] == "pie"


def test_histogram_builder(bank_df):
    spec = ChartSpec(chart_type="histogram", title="Balance dist", x="Balance", bins=15)
    result = execute_spec(bank_df, spec, _meta(bank_df))
    assert result["ok"]
    assert len(result["option"]["xAxis"]["data"]) == 15


def test_box_builder(bank_df):
    spec = ChartSpec(chart_type="box", title="Balance by churn", x="Churn", y="Balance")
    result = execute_spec(bank_df, spec, _meta(bank_df))
    assert result["ok"]
    assert result["option"]["series"][0]["type"] == "boxplot"


def test_scatter_builder(bank_df):
    spec = ChartSpec(chart_type="scatter", title="Balance vs amount", x="Balance", y="TransactionAmount", group="Churn")
    result = execute_spec(bank_df, spec, _meta(bank_df))
    assert result["ok"]
    assert len(result["option"]["series"]) >= 1


def test_heatmap_builder(bank_df):
    spec = ChartSpec(chart_type="heatmap", title="Correlations")
    result = execute_spec(bank_df, spec, _meta(bank_df))
    assert result["ok"]
    assert result["option"]["series"][0]["data"]


def test_grouped_bar_builder(bank_df):
    spec = ChartSpec(chart_type="grouped_bar", title="Products by churn", x="NumOfProducts", group="Churn")
    result = execute_spec(bank_df, spec, _meta(bank_df))
    assert result["ok"]
