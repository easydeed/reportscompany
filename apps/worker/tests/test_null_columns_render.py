"""
D-090 — a NULL database column renders as the word "None" in the PDF.

HOW IT WAS FOUND, WHICH IS THE POINT
------------------------------------
Not by looking for it. The root-suite rewrite (D-089) replaced hand-built
fixtures with the real builder, and one of the rewritten cases passes every
optional field as an explicit `None` rather than omitting it — because that is
what a nullable column with no value looks like by the time it reaches here.
Three of five themes then rendered, in the agent block of a customer-facing
report:

    ☎ None      ✉ None

THE CONSTRUCT
-------------
`d.get(k, "")` returns the default only when the key is MISSING. When the key
exists holding None — a row from a `LEFT JOIN`, a nullable column, a JSON field
explicitly set to null — it returns None, and Jinja prints that as "None".

`_build_agent_context` already carried a comment explaining exactly this, above
`title`, which was hardened for D-066/D-067. The lines immediately below it —
`phone`, `email`, `name`, `company_name`, `company_tagline` — were not. §0.6 says
to grep for the CONSTRUCT rather than the symptom and re-run the check after the
fix; this is the cost of having done the first half.

The survey found the same shape in `_build_property_context`, including a worse
instance: `street`, `city` and `state` are interpolated into `full_address`, so a
NULL there is not a blank on a detail line, it is

    "None, La Verne, CA 91750"

on the cover of all five themes. Also `owner_name`, `county`, `apn`,
`property_type` and `legal_description`, each written as
`a.get(k, "") or b.get(k, "")` — where the LAST term's None becomes the value of
the whole expression.

WHAT IS DELIBERATELY NOT CHANGED
--------------------------------
`latitude` and `longitude` stay None-able. There, None is a real value meaning
"no coordinates", and `_build_images_context` branches on it to skip the aerial
map. Collapsing them to "" would turn a meaningful absence into a falsy string
and change nothing except the type. **The defect is not "None exists in the
context" — it is "None reaches a template that prints it".**
"""
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

os.environ.setdefault("DATABASE_URL", "postgresql://fake/fake")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")

from worker.property_builder import PropertyReportBuilder, THEME_TEMPLATES  # noqa: E402

THEMES = list(THEME_TEMPLATES.keys())

BASE = {
    "property_address": "123 Test St",
    "property_city": "Test City",
    "property_state": "CA",
    "property_zip": "90210",
}

# The fields that come from nullable columns and end up as TEXT on the page.
# `latitude`/`longitude` are excluded on purpose — see the module docstring.
NULLABLE_TEXT_INPUTS = [
    ("property_address", "street"),
    ("property_city", "city"),
    ("property_state", "state"),
    ("property_zip", "zip_code"),
    ("owner_name", "owner_name"),
    ("property_county", "county"),
    ("apn", "apn"),
    ("property_type", "property_type"),
    ("legal_description", "legal_description"),
]

AGENT_TEXT_FIELDS = ["name", "title", "phone", "email", "company_name",
                     "company_tagline"]


def render(theme, report_data):
    return PropertyReportBuilder({**report_data, "theme": theme}).render_html()


# ── the agent block: the three-theme leak that started this ─────────────────

@pytest.mark.parametrize("theme", THEMES)
def test_a_null_phone_does_not_print_None_in_the_agent_block(theme, capsys):
    """
    THE REGRESSION, at the exact shape a database produces. Not an absent key —
    a present key holding None, which is what `phone TEXT NULL` gives you.
    """
    html = render(theme, {
        **BASE,
        "agent": {"name": "Agent", "phone": None, "email": None},
    })
    assert ">None<" not in html, (
        f"{theme}: a NULL agent phone/email rendered as the word None"
    )


def test_every_text_field_of_the_agent_context_collapses_null_to_empty():
    """
    The construct, not the two symptoms. Asserted on the CONTEXT rather than the
    rendered HTML, because a field no template currently prints is still a
    field the next template will print.
    """
    ctx = PropertyReportBuilder({
        **BASE,
        "agent": {f: None for f in AGENT_TEXT_FIELDS},
    })._build_agent_context()

    leaked = [f for f in AGENT_TEXT_FIELDS if ctx.get(f) is None]
    assert leaked == [], (
        f"agent context fields still None when the input key exists holding "
        f"None: {leaked}. `.get(k, '') `returns None for a present-but-null "
        f"key; use `.get(k) or ''`."
    )


# ── the property block, including the address the cover prints ──────────────

@pytest.mark.parametrize("field,context_key", NULLABLE_TEXT_INPUTS)
def test_a_null_property_field_collapses_to_empty(field, context_key):
    ctx = PropertyReportBuilder({**BASE, field: None})._build_property_context()
    assert ctx.get(context_key) is not None, (
        f"report_data[{field!r}] = None produced property.{context_key} = None"
    )


@pytest.mark.parametrize("field,context_key", NULLABLE_TEXT_INPUTS)
def test_a_null_sitex_field_collapses_to_empty(field, context_key):
    """
    The second half of each `or` chain. `a.get(k, "") or b.get(k, "")` looks
    guarded and is not: when the fallback is the one holding None, None is the
    value of the whole expression.
    """
    ctx = PropertyReportBuilder({
        **BASE,
        "sitex_data": {context_key: None, "owner_name": None, "county": None,
                       "apn": None, "property_type": None,
                       "legal_description": None},
    })._build_property_context()
    assert ctx.get(context_key) is not None, (
        f"sitex_data[{context_key!r}] = None produced property.{context_key} = None"
    )


@pytest.mark.parametrize("theme", THEMES)
def test_a_null_street_does_not_appear_inside_the_address(theme):
    """
    THE WORST INSTANCE. `full_address` is an f-string over four fields, so a
    NULL street is not a blank line on a detail table — it is the word "None"
    inside the address on the cover page. Measured before the fix: all five.
    """
    html = render(theme, {**BASE, "property_address": None})
    assert "None," not in html, (
        f"{theme}: a NULL street address rendered as 'None,' inside the "
        f"property address"
    )


def test_the_full_address_of_an_all_null_property_is_not_a_row_of_Nones():
    ctx = PropertyReportBuilder({
        "property_address": None, "property_city": None,
        "property_state": None, "property_zip": None,
    })._build_property_context()
    assert "None" not in ctx["full_address"], ctx["full_address"]


# ── the absence that must stay an absence ───────────────────────────────────

def test_coordinates_are_still_allowed_to_be_none():
    """
    THE GUARD ON THE FIX. Sweeping every None to "" would be the easy version
    and would break the aerial page: `_build_images_context` tests
    `property.latitude` to decide whether a map can be produced, and "" is
    falsy but is not a missing coordinate — it is a coordinate-shaped string
    that a future `float()` would choke on.
    """
    ctx = PropertyReportBuilder(BASE)._build_property_context()
    assert ctx["latitude"] is None
    assert ctx["longitude"] is None
