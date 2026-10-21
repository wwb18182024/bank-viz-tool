from app.core.metadata import extract_metadata
from app.core.plan_schema import ChartSpec
from app.core.plan_validator import dedupe, filter_plan, validate_spec


def _meta(bank_df):
    return extract_metadata(bank_df)


def test_reject_identifier_on_axis(bank_df):
    spec = ChartSpec(chart_type="bar", title="IDs", x="CustomerID", agg="count")
    ok, reason = validate_spec(spec, _meta(bank_df))
    assert not ok and "Identifier" in reason


def test_reject_unknown_chart_type(bank_df):
    spec = ChartSpec(chart_type="radar3d", title="x", x="Geography")
    ok, _ = validate_spec(spec, _meta(bank_df))
    assert not ok


def test_reject_unknown_column(bank_df):
    spec = ChartSpec(chart_type="bar", title="x", x="NotAColumn")
    ok, _ = validate_spec(spec, _meta(bank_df))
    assert not ok


def test_reject_scatter_with_categorical(bank_df):
    spec = ChartSpec(chart_type="scatter", title="x", x="Geography", y="Balance")
    ok, _ = validate_spec(spec, _meta(bank_df))
    assert not ok


def test_reject_pie_high_cardinality(bank_df):
    spec = ChartSpec(chart_type="pie", title="x", x="Balance")  # numeric pseudo-cat with many values
    ok, reason = validate_spec(spec, _meta(bank_df))
    assert not ok


def test_reject_donut_high_cardinality(bank_df):
    spec = ChartSpec(chart_type="donut", title="x", x="Balance")
    ok, _ = validate_spec(spec, _meta(bank_df))
    assert not ok


def test_reject_horizontal_bar_without_x(bank_df):
    spec = ChartSpec(chart_type="horizontal_bar", title="x", y="Balance", agg="mean")
    ok, reason = validate_spec(spec, _meta(bank_df))
    assert not ok and "requires an X column" in reason


def test_reject_stacked_area_without_group(bank_df):
    spec = ChartSpec(chart_type="stacked_area", title="x", x="Geography")
    ok, reason = validate_spec(spec, _meta(bank_df))
    assert not ok and "group" in reason.lower()


def test_accept_valid_specs(bank_df):
    meta = _meta(bank_df)
    specs = [
        ChartSpec(chart_type="bar", title="Mean balance by geography", x="Geography", y="Balance", agg="mean",
                  rationale="customer segmentation balance geography"),
        ChartSpec(chart_type="box", title="Balance by churn", x="Churn", y="Balance", rationale="risk churn balance"),
        ChartSpec(chart_type="histogram", title="Age distribution", x="Age", bins=10, rationale="segmentation age"),
    ]
    accepted, rejected = filter_plan(specs, meta)
    assert len(accepted) == 3 and not rejected


def test_dedupe():
    a = ChartSpec(chart_type="bar", title="a", x="Geography", y="Balance", agg="mean")
    b = ChartSpec(chart_type="bar", title="b (duplicate)", x="Geography", y="Balance", agg="mean")
    assert len(dedupe([a, b])) == 1


def test_banking_themes_rank_first(bank_df):
    generic = ChartSpec(chart_type="bar", title="Count of rows", x="Gender", agg="count", rationale="counts")
    themed = ChartSpec(chart_type="box", title="Credit limit by churn risk", x="Churn", y="CreditLimit",
                       rationale="risk exposure churn analysis")
    accepted, _ = filter_plan([generic, themed], _meta(bank_df))
    assert accepted[0].title.startswith("Credit limit")
