"""
D-137 — a default in a property report is a claim.

    "pool":       sitex_data.get("pool") or "No"
    "tax_status": sitex_data.get("tax_status") or "Current"

Neither key is written by SiteX's model or the wizard's payload (D-135), so
the `or` was not a fallback — it was the only path, and **every property
report ever generated stated that the home has no pool and that its taxes are
current.** Printed in the same type and the same table as the APN and the
legal description, which are real.

A dash says *we don't know*. `No` and `Current` say *we checked*.

TWO LAYERS, AND FIXING ONE LEAVES THE OTHER
-------------------------------------------
The templates carried their own: `{{ property.tax_status | default('Current') }}`,
`{{ stats.piq.stories | default('0') }}`, `{{ 'Yes' if comp.pool else 'No' }}`.
The construct exists in Python and in Jinja, so the gate checks both — §0.6's
*grep for the construct, not the symptom*, across a language boundary.

WHAT IS AND IS NOT A CLAIM
--------------------------
`report_type='seller'` and `language='en'` are configuration: they describe
what we are producing, not what is true of someone's house. `'-'`, `''`, `'?'`
and `'N/A'` are honest absences. Everything else asserts, and each one needs a
reason recorded or it fails.
"""
import ast
import os
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "apps/api/src"))

os.environ.setdefault("DATABASE_URL", "postgresql://fake/fake")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")

from api.services.sitex import PropertyData  # noqa: E402
from worker.property_builder import (  # noqa: E402
    ABSENT, PropertyReportBuilder, THEME_TEMPLATES, _tri_state_bool,
)

SRC = Path(__file__).resolve().parents[1] / "src/worker"
TEMPLATES = SRC / "templates/property"

#: Spellings that admit ignorance rather than asserting.
HONEST = {"", "-", "–", "—", "?", "N/A", "n/a", "Unknown", "TBD",
          # A column HEADING that names the quantity without characterising
          # it. "Sale Price" over an asking price is a claim; "Price" is not.
          "Price"}

#: The holders whose values are facts about SOMEBODY'S HOUSE. A default on a
#: brand colour, an agent's job title or a data-source line is about us and is
#: not this rule's business — scoping by holder rather than allow-listing the
#: rest keeps the gate's output entirely findings, which is the difference
#: between a gate that gets read and one that gets skimmed (D-135).
PROPERTY_HOLDERS = ("sitex_data", "comp", "property", "stats", "area", "piq")

#: Property-field defaults that are asserted anyway, each with its reason.
ALLOWED = {
    "Single Family":
        "property_type's fallback in four themes; teal spells it in full. "
        "See the entry below.",
    "Single Family Residential":
        "property_type's template fallback. It IS produced by both paths "
        "(D-135), so the default is unreachable — recorded rather than "
        "removed, because removing an unreachable default is churn and "
        "leaving it undocumented is how the next reader assumes it fires.",
    "Active":
        "comp status. Written by the API's projection AND the wizard's "
        "payload, so this is a genuine last resort rather than the only "
        "path — which is the whole distinction D-137 turns on.",
    "Sold":
        "comp.sold_date_label; set per comp from status on every path",
    # "0.1 mi" / "0.5 mi" / "1.2 mi" WERE EXCUSED HERE, with the note "delete
    # the builder; do not launder the default". The builder is deleted
    # (D-136), so the excuse has nothing to excuse and this test says so —
    # which is the half of a baseline that usually rots quietly.
    # "0" WAS EXCUSED HERE for `stats.piq.distance | default('0')` — the
    # subject's distance from itself IS zero, a measurement rather than a
    # stand-in for absence. The `default('0')` is gone: that cell now goes
    # through `format_measure`, which renders the literal 0 as "0" (checked
    # in the render, all five themes). Same output, no default to excuse.
}


def _on_a_property_holder(call):
    return any(h in ast.unparse(call.func.value) for h in PROPERTY_HOLDERS)


def _string_defaults_in(path: Path):
    """`<property holder>.get(k) or '<str>'` and `.get(k, '<str>')`."""
    out = []
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if (isinstance(node, ast.BoolOp) and isinstance(node.op, ast.Or)
                and isinstance(node.values[-1], ast.Constant)
                and isinstance(node.values[-1].value, str)):
            first = node.values[0]
            if (isinstance(first, ast.Call)
                    and isinstance(first.func, ast.Attribute)
                    and first.func.attr == "get"
                    and _on_a_property_holder(first)):
                out.append((node.lineno, node.values[-1].value))
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                and node.func.attr == "get" and len(node.args) == 2
                and isinstance(node.args[1], ast.Constant)
                and isinstance(node.args[1].value, str)
                and _on_a_property_holder(node)):
            out.append((node.lineno, node.args[1].value))
    return out


TEMPLATE_DEFAULT = re.compile(
    r"\{\{\s*(?:" + "|".join(PROPERTY_HOLDERS) + r")\.[\w.]+"
    r"[^}]*?\|\s*default\(\s*'([^']*)'\s*\)")


def _template_defaults_in(path: Path):
    """`{{ <property holder>.… | default('<str>') }}`."""
    return TEMPLATE_DEFAULT.findall(path.read_text(encoding="utf-8"))


# ── layer 1 · the builder ─────────────────────────────────────────────────

@pytest.mark.parametrize("module", ["property_builder.py", "consumer_report_data.py"])
def test_no_python_default_asserts_a_fact_about_the_property(module):
    path = SRC / module
    claims = sorted({v for _, v in _string_defaults_in(path)
                     if v not in HONEST and v not in ALLOWED})
    assert not claims, (
        f"{module} defaults to {claims}, which state things about a specific "
        f"person's property with nothing behind them. Use ABSENT, or add each "
        f"to ALLOWED with the reason it is not a claim."
    )


def test_the_allowed_list_does_not_outlive_the_code():
    """An excuse for a default nobody writes any more is one nobody rechecks."""
    live = set()
    for module in ("property_builder.py", "consumer_report_data.py"):
        live |= {v for _, v in _string_defaults_in(SRC / module)}
    for t in THEME_TEMPLATES.values():
        live |= set(_template_defaults_in(TEMPLATES / t))
    stale = sorted(set(ALLOWED) - live)
    assert not stale, f"ALLOWED excuses defaults that no longer exist: {stale}"


# ── layer 2 · the templates, where the same construct lives in Jinja ──────

@pytest.mark.parametrize("theme", sorted(THEME_TEMPLATES))
def test_no_template_default_asserts_a_fact_about_the_property(theme):
    found = sorted({d for d in _template_defaults_in(TEMPLATES / THEME_TEMPLATES[theme])
                    if d not in HONEST and d not in ALLOWED})
    assert not found, (
        f"{theme} renders `| default({found})`. Fixing only the builder leaves "
        f"the template asserting the same thing — the construct exists in both "
        f"languages."
    )


# ── the tri-state, which is the distinction the bug collapsed ────────────

@pytest.mark.parametrize("raw,expected", [
    (None, None), ("", None),                 # absent
    ("None", False), ("No", False), (False, False),   # a genuine negative —
    ("Yes", True), ("yes", True), (True, True),       # SiteX spells "no pool"
    ("true", True), (1, True), (0, False),            # as the STRING "None"
])
def test_unknown_is_not_collapsed_into_no(raw, expected):
    """`comp.get("pool", "No") == "Yes"` turned three states into two.

    The subtle half: SiteX's literal `"None"` means *no pool*, which IS a
    negative and must stay False. D-120 got this backwards — it read the
    string as truthy and reported a pool. Absent and "None" are different.
    """
    assert _tri_state_bool(raw) is expected


# ── the render, on a fixture production can actually produce ─────────────

@pytest.fixture(scope="module")
def producible():
    """Only keys a producer writes. A fixture that invents `pool` is how
    D-120 was filed against a state production cannot enter — and how this
    fix looked unapplied until the render script was corrected too."""
    data = {k: v for k, v in {
        "latitude": 34.1008, "longitude": -117.7678, "bedrooms": 2,
        "bathrooms": 1.0, "sqft": 786, "lot_size": 6155, "year_built": 1949,
        "assessed_value": 428248, "tax_amount": 5198.0,
    }.items() if k in PropertyData.model_fields}
    assert data, "the fixture filtered itself empty"
    return data


@pytest.mark.parametrize("theme", sorted(THEME_TEMPLATES))
def test_a_report_with_no_pool_data_does_not_say_the_home_has_no_pool(
        theme, producible):
    ctx = PropertyReportBuilder({"sitex_data": producible})._build_property_context()
    assert ctx["pool"] == ABSENT
    assert ctx["tax_status"] == ABSENT
    html = PropertyReportBuilder(
        {"sitex_data": producible, "theme": theme, "comparables": []}).render_html()
    for claim in ("Pool/Spa:</td><td class=\"val\">None",
                  "Tax Status:</td><td class=\"val\">Current"):
        assert claim not in html, f"{theme} still asserts: {claim}"


def test_the_numeric_rows_show_absence_rather_than_zero(producible):
    """A house with zero storeys is not a thing, and a pool count of 0 on an
    unwritten field is the same claim as "No" one table up (D-120)."""
    stats = PropertyReportBuilder(
        {"sitex_data": producible, "comparables": [{"price": 470000}]}
    )._build_stats_context()
    # `medium`, not `low`: D-119 fills the Medium column for a single comp and
    # blanks the other two, so asserting ABSENT on `low` here would pass
    # because the COLUMN is empty and say nothing about stories or pools —
    # the same vacuous-pass this file is named after, one level up.
    for slot in ("piq", "medium"):
        assert stats[slot]["stories"] == ABSENT
        assert stats[slot]["pools"] == ABSENT


def test_a_real_negative_still_reads_as_a_negative():
    """The fix must not turn "we know there is no pool" into "we don't know"."""
    stats = PropertyReportBuilder(
        {"sitex_data": {"pool": "None", "sqft": 786},
         "comparables": [{"price": 1, "pool": "Yes"}]}
    )._build_stats_context()
    assert stats["piq"]["pools"] == 0
    # D-119: ONE comp fills the Medium column, not Low. The median of a
    # one-element set is that element; a Low and a High would imply a spread
    # that does not exist, so those columns are blank. This test is about the
    # comp's pool value reading as a real negative, not about which column it
    # lands in — but it asserted on `low` and would now pass vacuously against
    # `-` if the assertion were loosened instead of moved.
    assert stats["medium"]["pools"] == 1
    assert stats["low"]["pools"] == ABSENT and stats["high"]["pools"] == ABSENT
