"""The guard for D-108, and the reason it is a walk rather than forty assertions.

The market and property templates are being replaced. A test that asserts
"macros.jinja2 line 71 renders Studio" leaves with the file it names; the forty
corrected conditionals leave with it too, and the replacement set can
reintroduce every one of them in silence. So this walks whatever templates are
on disk, derives the numeric field names from what the builders actually
produce, and parses each template with Jinja's own parser. Nothing here names a
file, a line, a CSS class or a fragment of markup.

See `_zero_conditionals.py` for the three syntaxes it covers and why.

THE RENDERED HALF IS DELIBERATELY SMALL. Two tests below do render, and they
assert on the WORDS a zero produces — "Studio", "New" — which is a copy
decision that a replacement template is entitled to make differently. They are
pinned to the current templates and are expected to be rewritten with them.
The structural gate is the part that is not.
"""
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from _zero_conditionals import (  # noqa: E402
    EXEMPT,
    audit_all,
    audit_python,
    audit_template,
    numeric_leaf_names,
    unexempt,
    unused_exemptions,
)
from jinja2 import Environment  # noqa: E402

from worker.market_builder import MarketReportBuilder  # noqa: E402


# ── the structural gate ─────────────────────────────────────────────────────

def test_no_template_decides_a_numeric_by_its_truthiness():
    """
    THE GATE THAT OUTLIVES THE TEMPLATES.

    `{% if value %}` is false for 0, so a real zero renders as nothing: a
    studio with no bed count, a same-day sale with no DOM, a market with
    nothing for sale and no months-of-supply figure. Giving the conditional an
    `{% else %}` is what makes the zero a rendering decision instead of an
    accident — this does not care WHAT the else says.

    If this fails on a field whose zero genuinely cannot happen, add it to
    `EXEMPT` in `_zero_conditionals.py` WITH THE REASON. Do not delete the
    finding.
    """
    findings = unexempt(audit_all())
    assert findings == [], (
        "these render nothing when the value is a real 0:\n  "
        + "\n  ".join(str(f) for f in findings)
    )


def test_no_statistic_is_computed_over_a_filter_that_drops_its_zeros():
    """
    THE SAME GATE, IN PYTHON, AND THE HALF THAT SAYS NOTHING WHEN IT IS WRONG.

    `[l["days_on_market"] for l in closed if l.get("days_on_market")]` excludes
    every same-day sale from the average of how long sales take. A template
    that hides a zero shows a visibly missing chip; an average that drops its
    zeros just reads high, on a page that presents it as a measurement.

    Nine of these were live when this was written, and D-105 is what made the
    zero reachable — a fix in one place turning a dormant defect on in another
    is the reason this is a walk and not nine edits.
    """
    findings = unexempt(audit_python())
    assert findings == [], (
        "these statistics are computed over a list their zeros were filtered "
        "out of:\n  " + "\n  ".join(str(f) for f in findings)
    )


def test_the_exemption_list_does_not_outlive_what_it_excused():
    """
    An allowlist nothing uses is an allowlist nobody rechecks — and one that
    can be padded in advance to pre-clear a defect that has not been filed.
    Every entry must still be covering a real conditional.
    """
    stale = unused_exemptions(audit_all() + audit_python())
    assert stale == [], (
        f"EXEMPT entries no template relies on any more: {stale}. "
        f"Remove them; if the conditional comes back it can be re-argued then."
    )


def test_a_bare_comprehension_filter_is_caught_and_an_explicit_one_is_not(tmp_path):
    """
    The Python walk, both directions, on real source rather than on a string:
    the bare filter is reported and `is not None` clears it.
    """
    import _zero_conditionals as mod
    scratch = tmp_path / "worker"
    scratch.mkdir()
    (scratch / "m.py").write_text(
        "def f(rows):\n"
        "    bad = [r['days_on_market'] for r in rows if r.get('days_on_market')]\n"
        "    ok = [r['days_on_market'] for r in rows if r.get('days_on_market') is not None]\n"
        "    return bad, ok\n")
    # Derive the names BEFORE redirecting REPO — the derivation imports the
    # builders through that same path.
    names = numeric_leaf_names()
    original_roots, original_repo = mod.PY_ROOTS, mod.REPO
    mod.REPO, mod.PY_ROOTS = tmp_path, ("worker",)
    try:
        found = audit_python(names)
    finally:
        mod.REPO, mod.PY_ROOTS = original_repo, original_roots
    assert [f.expr for f in found] == ["days_on_market"], (
        f"expected exactly the bare filter, got {found}"
    )


def test_the_numeric_names_are_derived_from_the_builders_not_listed():
    """
    The whole gate rests on this set. A hand-written list of numeric-looking
    names is the mistake this repo keeps re-finding, so the names come from
    walking real built contexts — which means a new field the builders add is
    in scope without anyone remembering to add it.

    Asserted as a property, not a pinned list: the point is that it is derived.
    """
    names = numeric_leaf_names()
    # Fields no one typed into this file: they are here because the builders
    # put numbers in them.
    for expected in ("beds", "days_on_market", "months_of_inventory",
                     "avg_dom", "total_count", "count", "year_built"):
        assert expected in names, f"{expected!r} missing — the derivation broke"
    assert len(names) > 20, f"only {len(names)} numeric names — derivation broke"


# ── the gate can fail: three regressions, applied to a real template ────────

REGRESSIONS = [
    pytest.param(
        "{% macro m(listing) %}{% if listing.beds %}{{ listing.beds }} bd{% endif %}{% endmacro %}",
        "beds", id="bare-if-hides-a-studio"),
    pytest.param(
        "{% macro m(l) %}{{ l.days_on_market if l.days_on_market else '-' }}{% endmacro %}",
        "days_on_market", id="ternary-hides-a-same-day-sale"),
    pytest.param(
        "{% macro m(bands) %}{% for b in bands | selectattr('count') %}{{ b }}{% endfor %}{% endmacro %}",
        "count", id="selectattr-drops-the-empty-band"),
]


@pytest.mark.parametrize("source,leaf", REGRESSIONS)
def test_the_gate_catches_the_defect_in_each_of_its_three_syntaxes(source, leaf, tmp_path):
    """
    A gate that has never been seen to fail is a gate nobody has tested. Each
    of these is a shape this repo has actually shipped — the third one twice,
    the second time days after the first was written up.
    """
    from _zero_conditionals import TEMPLATES
    scratch = TEMPLATES / "_gate_regression_scratch.jinja2"
    scratch.write_text(source, encoding="utf-8")
    try:
        found = audit_template(scratch, numeric_leaf_names(), Environment())
    finally:
        scratch.unlink()
    assert [f.expr.split(".")[-1] for f in found] == [leaf], (
        f"the gate did not see the defect in {source!r}"
    )


def test_an_else_branch_is_what_clears_it_not_the_words_in_it(tmp_path):
    """
    The counterpart. The same conditional with an else passes, whatever the
    else says — so a replacement template may render a zero however it likes
    and this gate stays quiet. That is the property that lets it survive one.
    """
    from _zero_conditionals import TEMPLATES
    scratch = TEMPLATES / "_gate_regression_scratch.jinja2"
    scratch.write_text(
        "{% macro m(listing) %}{% if listing.beds is not none %}"
        "{% if listing.beds %}{{ listing.beds }} bd{% else %}anything at all{% endif %}"
        "{% endif %}{% endmacro %}", encoding="utf-8")
    try:
        found = audit_template(scratch, numeric_leaf_names(), Environment())
    finally:
        scratch.unlink()
    assert found == [], f"an else-covered conditional was reported: {found}"


def test_a_deliberate_fallback_chain_is_not_reported(tmp_path):
    """
    `{% if close %}…{% elif list %}…{% else %}—{% endif %}` is a fallback
    chain, not an absence check. The first version of this walk judged the
    elif on its own empty `else_` and failed two correct chains; the else
    belongs to the whole chain.
    """
    from _zero_conditionals import TEMPLATES
    scratch = TEMPLATES / "_gate_regression_scratch.jinja2"
    scratch.write_text(
        "{% macro m(s) %}{% if s.median_close_price %}a"
        "{% elif s.median_list_price %}b{% else %}&mdash;{% endif %}{% endmacro %}",
        encoding="utf-8")
    try:
        found = audit_template(scratch, numeric_leaf_names(), Environment())
    finally:
        scratch.unlink()
    assert found == [], f"a fallback chain was reported as a defect: {found}"


# ── the builder half: `or` is the same defect in Python ─────────────────────

def _one_listing(**over):
    base = {"street_address": "1 A St", "city": "Irvine", "list_price": 900000,
            "bedrooms": 3, "bathrooms": 2, "sqft": 1500, "status": "Active",
            "days_on_market": 12}
    base.update(over)
    return {"report_type": "new_listings_gallery", "city": "Irvine",
            "lookback_days": 30, "listings": [base], "metrics": {}, "counts": {},
            "branding": {}}


def test_a_studio_survives_the_builder_as_zero_not_as_none():
    """
    THE HALF THAT WOULD HAVE MADE THE TEMPLATE FIX WRONG.

    `item.get("bedrooms") or item.get("beds", 0)` returns 0 for a studio AND 0
    for a listing with no bed count — it destroys the distinction before the
    template sees it. With the old `{% if listing.beds %}` both were hidden, so
    it read as correct. Rendering the zero as "Studio" without fixing this
    would have printed "Studio" over missing data.
    """
    ctx = MarketReportBuilder(_one_listing(bedrooms=0))._build_listings_context()
    assert ctx["items"][0]["beds"] == 0, "a studio reached the template as something else"


def test_a_missing_bed_count_survives_the_builder_as_none_not_as_zero():
    data = _one_listing()
    del data["listings"][0]["bedrooms"]
    ctx = MarketReportBuilder(data)._build_listings_context()
    assert ctx["items"][0]["beds"] is None, (
        "missing bed data arrived as 0 — the template will call it a studio"
    )


def test_a_zero_avg_dom_is_not_swallowed_by_the_metric_fallback():
    """
    Newly reachable: D-105 made the report read the feed's own DOM, and a
    same-day sale reports 0. `metrics.get("avg_dom") or metrics.get("median_dom")`
    walked straight past it to None, which the page renders as no data at all.
    """
    data = _one_listing()
    data["metrics"] = {"avg_dom": 0}
    assert MarketReportBuilder(data)._build_stats_context()["avg_dom"] == 0


# ── the rendered half: pinned to today's copy, expected to be rewritten ─────

def _render(**over):
    return MarketReportBuilder(_one_listing(**over)).render_html()


def test_zero_bedrooms_renders_as_a_studio():
    html = _render(bedrooms=0)
    assert "Studio" in html, "a studio rendered with no bed count at all"


def test_zero_days_on_market_renders_as_new():
    html = _render(days_on_market=0)
    assert re.search(r">\s*New\s*<", html), "a same-day listing rendered with no DOM"


def test_an_empty_result_set_says_so_in_the_terms_of_the_search():
    """
    total_count 0 is a result, not a missing field. The report renders and
    names what was searched, so an empty market and an over-tight filter are
    told apart. Whether such a report should be SENT is D-110, not this.
    """
    data = _one_listing()
    data["listings"] = []
    data["filters_label"] = "2+ beds, SFR, under $1.5M"
    html = MarketReportBuilder(data).render_html()
    assert "No listings matched this search" in html
    assert "2+ beds, SFR, under $1.5M" in html, "the empty state did not say what was searched"
    assert "Irvine" in html
