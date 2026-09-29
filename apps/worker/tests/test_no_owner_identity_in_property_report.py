"""
E1 / D-116 — the property report must not print the owner's identity.

WHY THIS IS STRUCTURAL RATHER THAN A RENDER ASSERTION
-----------------------------------------------------
The fix deleted four rows from five templates. A test that renders those five
and greps for `HERNANDEZ GERARDO J` passes for as long as nobody adds a sixth
template, renames a field, or reinstates the block somewhere else on the page —
and the whole point is that the next person will not know this rule exists.

So the gate walks EVERY template under templates/property/ and fails on any
reference to a forbidden context key, whatever the template is called and
whatever page it lives on. A new theme inherits the rule on the day it is
added. §0.6: make the property structural instead of somebody's diligence.

WHAT IS FORBIDDEN, AND WHY MAILING ADDRESS IS ON THE LIST
---------------------------------------------------------
`owner_name` and `secondary_owner` are the assessor roll's names. Jerry's
instruction was "the name and the framing go; keep APN, county, legal
description, tax and assessment".

`mailing_address` is not in either list, and it is removed, because for an
absentee owner it is not a fact about the property — it is where that person
lives. Leaving it would preserve exactly the disclosure E1 is about. It
defaulted to `full_address` when absent, so nothing is lost for an
owner-occupier. This is a judgement beyond the literal instruction and is
flagged as such; putting it back is one row per template.

THE CONTEXT KEYS ARE DELIBERATELY NOT DELETED
---------------------------------------------
`_build_property_context` still emits all three. They come from real columns on
`property_reports` that other surfaces read, and D-090's framing applies: the
defect is not "the value exists in the context", it is "the value reaches a
template that prints it". The template is the disclosure boundary, so that is
where the gate sits.

Checked separately, not assumed: `ai_overview._build_prompt` names every field
it sends and none of the three is among them, so the executive summary cannot
reintroduce the name through the model.
"""
import os
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

os.environ.setdefault("DATABASE_URL", "postgresql://fake/fake")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")

from worker.property_builder import PropertyReportBuilder, THEME_TEMPLATES  # noqa: E402

TEMPLATES = Path(__file__).resolve().parents[1] / "src/worker/templates/property"
THEMES = sorted(THEME_TEMPLATES)

FORBIDDEN = ("owner_name", "secondary_owner", "mailing_address")

# The framing half of E1: a seller's own home described as one they might buy.
FORBIDDEN_COPY = ("prospective property", "prospective home")


def property_templates():
    files = sorted(TEMPLATES.rglob("*.jinja2"))
    assert len(files) >= len(THEMES), f"expected at least {len(THEMES)}, found {len(files)}"
    return files


@pytest.mark.parametrize("path", property_templates(), ids=lambda p: p.name)
def test_no_property_template_references_an_owner_identity_field(path):
    text = path.read_text(encoding="utf-8")
    hits = [k for k in FORBIDDEN if re.search(rf"\b{k}\b", text)]
    assert not hits, (
        f"{path.relative_to(TEMPLATES)} references {hits}. The property report "
        "is delivered to a stranger through the consumer lead-capture funnel; "
        "assessor-roll identity does not go in it (D-116)."
    )


@pytest.mark.parametrize("path", property_templates(), ids=lambda p: p.name)
def test_no_property_template_calls_it_a_prospective_property(path):
    lower = path.read_text(encoding="utf-8").lower()
    hits = [c for c in FORBIDDEN_COPY if c in lower]
    assert not hits, (
        f"{path.relative_to(TEMPLATES)} says {hits}. The recipient owns the "
        "house; 'prospective' is the framing half of D-116."
    )


# ── the render side, which proves the templates above are the ones in use ───

@pytest.fixture(scope="module")
def renders():
    from test_property_production_render import report_data  # same fixture data
    return {t: PropertyReportBuilder(report_data(t)).render_html() for t in THEMES}


@pytest.mark.parametrize("theme", THEMES)
def test_the_owner_name_does_not_appear_in_the_rendered_report(theme, renders):
    from test_property_production_render import report_data
    data = report_data(theme)
    for value in (data["owner_name"], data["sitex_data"]["secondary_owner"],
                  data["sitex_data"]["mailing_address"]):
        assert value not in renders[theme], f"{theme} renders {value!r}"


@pytest.mark.parametrize("theme", THEMES)
def test_the_kept_parcel_fields_are_still_there(theme, renders):
    """Jerry kept APN, county, legal description, tax and assessment.

    Without this, deleting the whole page would pass the test above.
    """
    from test_property_production_render import report_data
    data = report_data(theme)
    html = renders[theme]
    for value in (data["apn"], data["property_county"], data["legal_description"]):
        assert value in html, f"{theme} lost {value!r}"
    assert "428,248" in html, f"{theme} lost the assessed value"


# ── D-116's own footgun, caught in the render and now gated ─────────────────

# Removing the owner rows left one theme's block holding a single row, so the
# fix moved parcel fields into it — and in bold, classic and elegant the block
# beside it already carried them. The first render showed APN, County and
# Legal Description twice on one page. Nothing would have caught that.
PAGE_HEADING = re.compile(
    r'(?:page-header-title|property-title)">Property Information'
    r'|>\s*PROPERTY INFORMATION\s*<'
)

FIELD_LABELS = (
    "APN", "County", "Census Tract", "Legal Description", "Legal", "Site Address",
    "Property Type", "Year Built", "Lot Size", "Bedrooms", "Bathrooms",
    "Square Feet", "Assessed Value", "Zoning", "Pool/Spa",
)


def property_page(html: str) -> str:
    """The one <section> carrying the property page's own heading.

    Matched on the heading INSIDE its title element, because every theme's
    contents page also contains the string "Property Information" — the
    accidental-selector trap, hit while writing this file.
    """
    pages = [p for p in html.split("<section") if PAGE_HEADING.search(p)]
    assert len(pages) == 1, f"expected one property page, found {len(pages)}"
    return pages[0]


@pytest.mark.parametrize("theme", THEMES)
def test_no_field_is_printed_twice_on_the_property_page(theme, renders):
    page = property_page(renders[theme])
    dupes = {
        label: n
        for label in FIELD_LABELS
        if (n := len(re.findall(rf">\s*{re.escape(label)}\s*:?\s*<", page))) > 1
    }
    assert not dupes, f"{theme}'s property page prints {dupes}"
