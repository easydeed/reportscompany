"""
E1 / D-116, as D-157 leaves it — WHERE the owner of record may appear.

WHAT CHANGED, AND WHY THIS FILE IS NOT SIMPLY DELETED
-----------------------------------------------------
D-116's rule was "no property template references an owner identity field",
and this file enforced it by walking every template. Jerry's D-157 decision
supersedes the blanket half: an agent running a report on a property
knowingly may see the owner of record, so the templates now legitimately
carry the block. The disclosure rule did not go away — it acquired a
condition. `mailing_address` did not acquire one and is still forbidden
outright, on both paths.

A blanket ban that is no longer true cannot just be relaxed to nothing,
because the property it was protecting is still real: a stranger on a lead
page must not be handed a name off the assessor roll. That property is now
asserted on the RENDERED consumer document, in
`test_consumer_names_the_requester.py`, which is the right place for it —
the templates are no longer the boundary, the audience flag is.

WHAT IS LEFT HERE, AND WHY IT IS STILL STRUCTURAL
-------------------------------------------------
The render test covers the five themes that exist today. It says nothing
about a sixth, and the failure mode this file was written for has not
changed: the next person will not know the rule exists. So the structural
gate stays and is narrowed to the shape of the new rule —

  * every template reference to `owner_name` / `secondary_owner` is reachable
    only under a branch that tests the audience, and
  * `mailing_address` is referenced by no template at all.

Parsed with Jinja's own parser rather than matched as text. A grep would be
answered by the comment sitting directly above each of those blocks, which
contains the word `mailing_address` while describing why it is absent —
§0.6's "a substring is not a construct", which this file's previous version
would have failed on.

WHY MAILING ADDRESS IS STILL ON THE LIST
----------------------------------------
For an absentee owner it is not a fact about the property — it is where that
person lives. Jerry: "mailing_address stays OUT on both paths." It defaulted
to `full_address` when absent, so nothing is lost for an owner-occupier.

Checked separately, not assumed: `ai_overview._build_prompt` names every
field it sends and none of the three is among them, so the executive summary
cannot reintroduce the name through the model.
"""
import os
import re
import sys
from pathlib import Path

import pytest
from jinja2 import Environment, nodes

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

os.environ.setdefault("DATABASE_URL", "postgresql://fake/fake")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")

from worker.property_builder import PropertyReportBuilder, THEME_TEMPLATES  # noqa: E402

TEMPLATES = Path(__file__).resolve().parents[1] / "src/worker/templates/property"
THEMES = sorted(THEME_TEMPLATES)

#: The five files a theme actually renders. Every other template under
#: `templates/property/` is a partial or a base, and none of them may carry
#: the block — there is nowhere in a partial to know the audience.
REPORT_TEMPLATES = {TEMPLATES / p for p in THEME_TEMPLATES.values()}

#: Allowed, but only behind an audience test.
CONDITIONAL = ("owner_name", "secondary_owner")

#: Allowed nowhere.
FORBIDDEN = ("mailing_address",)

#: What a branch must mention for the references under it to count as gated.
AUDIENCE = ("audience", "_audience")

# The framing half of E1: a seller's own home described as one they might buy.
FORBIDDEN_COPY = ("prospective property", "prospective home")


def property_templates():
    files = sorted(TEMPLATES.rglob("*.jinja2"))
    assert len(files) >= len(THEMES), f"expected at least {len(THEMES)}, found {len(files)}"
    missing = REPORT_TEMPLATES - set(files)
    assert not missing, f"THEME_TEMPLATES points at files that do not exist: {missing}"
    return files


def parse(path: Path):
    return Environment().parse(path.read_text(encoding="utf-8"))


def _refs(node, names):
    """Every reference to one of `names` anywhere under `node`.

    Identified by (name, lineno) so the two sets below can be compared. All
    three access shapes count: `property.owner_name`, `property['owner_name']`
    and a bare `owner_name`.
    """
    found = set()
    for n in node.find_all(nodes.Getattr):
        if n.attr in names:
            found.add((n.attr, n.lineno))
    for n in node.find_all(nodes.Getitem):
        arg = getattr(n.arg, "value", None)
        if arg in names:
            found.add((arg, n.lineno))
    for n in node.find_all(nodes.Name):
        if n.name in names:
            found.add((n.name, n.lineno))
    return found


def _mentions_audience(test) -> bool:
    return bool(_refs(test, AUDIENCE)) or any(
        n.name in AUDIENCE for n in test.find_all(nodes.Name)
    )


def _audience_gated(tree, names):
    """References that only render when some branch has tested the audience.

    `if_.body` ONLY. An `{% else %}` or `{% elif %}` under an audience test is
    the branch that runs for the OTHER audience, so anything in it is exactly
    what this is looking for. `find_all` recurses, so a nested `if` — which is
    how `secondary_owner` hangs off `owner_name` in all five themes — is
    covered by its parent.
    """
    gated = set()
    for if_ in tree.find_all(nodes.If):
        if _mentions_audience(if_.test):
            gated |= _refs(if_.test, names)
            for child in if_.body:
                gated |= _refs(child, names)
    return gated


@pytest.mark.parametrize("path", property_templates(), ids=lambda p: p.name)
def test_an_owner_identity_field_is_only_reachable_on_the_agent_path(path):
    """D-157. The block may exist; it may not be unconditional.

    This is the part the rendered-output gate cannot see. That gate renders
    the consumer path and finds no owner name — which is equally true when
    the template is correct and when the template is wrong but the consumer
    builder happens not to forward the field. Two defences, and this one
    asserts its own.
    """
    tree = parse(path)
    refs = _refs(tree, CONDITIONAL)
    ungated = refs - _audience_gated(tree, CONDITIONAL)
    assert not ungated, (
        f"{path.relative_to(TEMPLATES)} renders {sorted(ungated)} without "
        "testing the audience. The property report is delivered to a stranger "
        "through the consumer lead-capture funnel; assessor-roll identity "
        "reaches the agent path only (D-116, D-157)."
    )


@pytest.mark.parametrize("path", sorted(REPORT_TEMPLATES), ids=lambda p: p.name)
def test_every_theme_actually_has_the_owner_block(path):
    """Otherwise the test above is satisfied by deleting the block.

    Jerry asked for it back on the agent path in all five themes, not in
    whichever ones somebody got to.
    """
    refs = _refs(parse(path), CONDITIONAL)
    assert refs, (
        f"{path.relative_to(TEMPLATES)} has no owner-of-record block. The "
        "gate above passes trivially for a template that renders nothing, so "
        "this is the half that says the restore happened here too."
    )


@pytest.mark.parametrize("path", property_templates(), ids=lambda p: p.name)
def test_no_property_template_references_a_mailing_address(path):
    """Unconditional — there is no audience this is a property fact for.

    Parsed, not grepped: the comment above each owner block explains that
    `mailing_address` stays out, and says the words to do it.
    """
    refs = _refs(parse(path), FORBIDDEN)
    assert not refs, (
        f"{path.relative_to(TEMPLATES)} references {sorted(refs)}. For an "
        "absentee owner a mailing address is where a person lives, not a fact "
        "about the property — out on both paths (D-116)."
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
def test_the_mailing_address_does_not_appear_in_the_rendered_report(theme, renders):
    from test_property_production_render import report_data
    value = report_data(theme)["sitex_data"]["mailing_address"]
    assert value not in renders[theme], f"{theme} renders {value!r}"


@pytest.mark.parametrize("theme", THEMES)
def test_the_kept_parcel_fields_are_still_there(theme, renders):
    """Jerry kept APN, county, legal description, tax and assessment.

    Without this, deleting the whole page would pass the tests above.
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
    "Square Feet", "Assessed Value", "Zoning", "Pool/Spa", "Owner of Record",
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
