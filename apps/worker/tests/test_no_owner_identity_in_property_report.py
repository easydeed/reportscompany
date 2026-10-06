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

THIS FILE IS NOT COVERAGE FOR THE DISCLOSURE. READ THIS BEFORE TRUSTING IT.
---------------------------------------------------------------------------
The gate below checks that a branch MENTIONS the audience. It does not check
that the sense is right, and it cannot — `_audience != 'agent'` passes it.
That is one character away from putting a name off the assessor roll onto a
report a stranger requested, with every test in this file green.

The only thing standing between that edit and the disclosure is
`test_no_assessor_owner_name_reaches_a_consumer_report` in
`test_consumer_names_the_requester.py`, which RENDERS the consumer path and
greps the output. Confirmed by applying the inversion: this file stayed
green, two render tests fired.

The two halves cover different failures and neither is sufficient alone.
The render tests see the sense, on the five themes that exist. This file
sees a SIXTH theme added with no gate at all, which the render tests cannot,
because they only render the five. If you are here to delete the render half
because "the AST test already checks the owner block", you have it backwards.

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
from _template_chain import SELF_CONTAINED_THEMES, SHARED_THEMES, chain  # noqa: E402

TEMPLATES = Path(__file__).resolve().parents[1] / "src/worker/templates/property"
THEMES = sorted(THEME_TEMPLATES)

#: Every file a theme actually renders — entry files AND the shared
#: architecture they include. Resolved by parsing, so a theme moving onto the
#: shared file does not quietly drop out of this set.
#:
#: WHY THE SHARED FILE IS IN HERE AND NOT EXCLUDED AS A "PARTIAL". The old
#: comment said a partial may never carry the owner block, "because there is
#: nowhere in a partial to know the audience". `_v2/report.jinja2` is not a
#: partial — it is the document, and `audience` is in its context. What must
#: stay true is that the block is reachable only under an audience test,
#: which is exactly what the gate below asserts and which does not care
#: whether the file is one theme's or three themes'.
REPORT_TEMPLATES = {p for t in THEME_TEMPLATES for p in chain(t)}

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


@pytest.mark.parametrize("theme", SELF_CONTAINED_THEMES)
def test_every_self_contained_theme_actually_has_the_owner_block(theme):
    """Otherwise the test above is satisfied by deleting the block.

    Jerry asked for it back on the agent path in every theme, not in whichever
    ones somebody got to.

    SELF-CONTAINED THEMES ONLY, because a theme on the shared architecture
    does not gate the block in its TEMPLATE at all — see the test below.
    """
    refs = {r for p in chain(theme) for r in _refs(parse(p), CONDITIONAL)}
    assert refs, (
        f"{theme} has no owner-of-record block. The gate above passes "
        "trivially for a template that renders nothing, so this is the half "
        "that says the restore happened here too."
    )


@pytest.mark.parametrize("theme", SHARED_THEMES)
def test_the_shared_architecture_gates_the_owner_block_in_PYTHON(theme):
    """And that is STRONGER than an audience test in the template.

    Design's one page architecture builds page 2's rows in
    `_build_v2_context`, and the owner row is APPENDED only when the audience
    is the agent. So the consumer context does not contain the name —
    there is nothing for a template edit to reveal, and nothing for a flipped
    operator to leak. The `{% if audience %}` form this replaces was one
    character from a disclosure with every structural test green, which is
    what the big warning at the top of this file is about.

    Asserted as THREE things, because "the template does not mention it" alone
    would also be true of a build that dropped the owner of record entirely:

      1. no live template references an owner identity field at all
      2. the CONSUMER context carries no owner identity value
      3. the AGENT context does carry it

    1 is structural; 2 and 3 are read off the builder, not off a render, so
    they fail even if some future template stops printing what it is handed.
    """
    for path in chain(theme):
        refs = _refs(parse(path), CONDITIONAL)
        assert not refs, (
            f"{path.relative_to(TEMPLATES)} references {sorted(refs)}. On the "
            f"shared architecture the owner block is built in Python and the "
            f"template is handed finished rows; a template that names the "
            f"field has reintroduced the audience branch the file above "
            f"describes, and must then satisfy that gate instead."
        )

    from test_property_production_render import report_data

    def rows(audience):
        data = {**report_data(theme), "audience": audience}
        builder = PropertyReportBuilder(data)
        ctx = {
            "property": builder._build_property_context(),
            "agent": builder._build_agent_context(),
            "stats": builder._build_stats_context(),
            "comparables": builder._build_comparables_context(),
            "audience": audience,
            "prepared_for": "",
        }
        doc = builder._build_v2_context(ctx, list(builder.V2_PAGE_ORDER))
        return [r for g in doc["detail_groups"] for r in g["rows"]]

    owner = report_data(theme)["sitex_data"].get("owner_name") or \
        report_data(theme).get("owner_name")
    consumer_rows = rows("consumer")
    agent_rows = rows("agent")

    labels = {r["label"].lower() for r in consumer_rows}
    assert "owner of record" not in labels, (
        f"{theme}: the consumer context carries an owner-of-record row"
    )
    values = " ".join(str(r["value"]) for r in consumer_rows)
    for name in (owner, report_data(theme)["sitex_data"].get("secondary_owner")):
        if name:
            assert name not in values, (
                f"{theme}: {name!r} is in the consumer context's property rows"
            )

    assert "owner of record" in {r["label"].lower() for r in agent_rows}, (
        f"{theme}: the AGENT context has no owner-of-record row either, so "
        f"the assertion above is passing on a build that dropped the block"
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


#: The shared architecture labels every page on its own `<section>`, which
#: is a better locator than a heading and is used when it is there.
SHEET_CLASS = re.compile(r'class="sheet sheet-property"')


def property_page(html: str) -> str:
    """The one <section> that is the property page.

    TWO LOCATORS, AND THE FIRST ONE IS THE GOOD ONE. A theme on the shared
    architecture names each page on its `<section>`; a self-contained theme
    does not, so for those the page is matched on the heading INSIDE its title
    element — because every v1 theme's CONTENTS page also contains the string
    "Property Information", which is the accidental-selector trap this
    function was written for.

    Exactly one match either way, asserted, so a locator that stops matching
    fails here rather than passing an empty string to the caller — which is
    how "expected one property page, found 0" came to be the FIRST thing the
    architecture change reported, and the right thing for it to report.
    """
    sections = html.split("<section")
    pages = [s for s in sections if SHEET_CLASS.search(s)]
    if not pages:
        pages = [s for s in sections if PAGE_HEADING.search(s)]
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
