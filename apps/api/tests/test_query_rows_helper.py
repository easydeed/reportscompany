"""
The row helper is a test double, so it needs tests (D-091).

WHY THIS FILE EXISTS
--------------------
`_query_rows.row_for` is the thing standing between every API unit test and the
unpack errors that produced 29 of this suite's 39 failures. Three regressions
were run against it: reverting D-092 failed the right test, truncating rows to
the old 7-column shape failed 17 — and **removing its unknown-column guard
changed nothing**, because no existing test passes a bad column name.

An unexercised guard is a guard nobody knows is broken. So the guard gets its
own test, rather than a claim that it works.

The rule this is an instance of, from §0.6: a regression that produces no
failure is information about the COVERAGE, not proof the code is fine. The
honest response is to add the missing case, not to note the gap and move on.
"""
import pytest

from _query_rows import columns_of, row_for, row_dict
from api.services.usage import resolve_plan_for_account
from api.services.branding import get_brand_for_account


def test_it_reads_the_real_column_count_off_the_query():
    """
    THE ARITY THAT BROKE EVERYTHING. 15 for the plan query — 7 when these tests
    were written, plus the deferred-downgrade pair and the six per-product limit
    and override columns.
    """
    assert len(columns_of(resolve_plan_for_account)) == 15
    assert len(columns_of(get_brand_for_account)) == 3


def test_it_keeps_the_querys_own_order():
    cols = columns_of(resolve_plan_for_account)
    assert cols[:3] == ["plan_slug", "monthly_report_limit_override", "account_type"]
    assert cols[-1] == "property_reports_limit_override"


def test_it_resolves_an_AS_alias_rather_than_the_expression():
    """`p.monthly_report_limit AS plan_limit` is `plan_limit`, not `monthly_report_limit`."""
    assert "plan_limit" in columns_of(resolve_plan_for_account)


def test_named_values_land_in_the_right_positions():
    row = row_for(resolve_plan_for_account, plan_slug="pro", plan_limit=300)
    cols = columns_of(resolve_plan_for_account)
    assert row[cols.index("plan_slug")] == "pro"
    assert row[cols.index("plan_limit")] == 300
    assert len(row) == len(cols)


def test_unnamed_columns_default_to_none():
    row = row_dict(resolve_plan_for_account, plan_slug="free")
    assert row["plan_slug"] == "free"
    assert row["schedules_limit"] is None


def test_an_unknown_column_name_raises():
    """
    THE GUARD THE REGRESSION RUN FOUND UNEXERCISED.

    Without it, a typo or a renamed column silently produces an all-None row of
    the right width — which is worse than the failure it replaced, because the
    unpack succeeds and the test asserts against garbage.
    """
    with pytest.raises(AssertionError, match="no column"):
        row_for(resolve_plan_for_account, plan_slugg="free")


def test_asking_for_a_query_the_function_does_not_have_raises():
    """
    `get_brand_for_account` has one SELECT. Asking for a second must stop the
    test rather than return a guess — a partial column list produces a
    wrong-width tuple, which is the unpack error this module exists to remove.
    """
    with pytest.raises(AssertionError, match="SELECT literal"):
        columns_of(get_brand_for_account, index=3)
