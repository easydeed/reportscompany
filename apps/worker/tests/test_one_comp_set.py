"""
D-159 — one comparable set, and the document says so truthfully.

WHAT WAS WRONG
--------------
Eight caps and none of them knew about the others: 60 and 15 in the API, 25
and 15 in the worker, 6 in the consumer builder, 6 in the cards context,
`[:4]` in twenty-four template loops, and no cap at all on the analysis
table, the range or `total_comps`. The document printed

    "every one of the 15 appears on the Sales Comparables page"

and showed four, in every theme, with the range drawn over the eleven the
reader could not see — $500k–$850k beside four cards spanning
$500,000–$575,000. A seller could check 21% of the spread.

WHY THIS IS A GATE AND NOT A FIX
--------------------------------
The fix is one page and one constant; the PROPERTY is "every count in this
document is the same count", and that property was violated for as long as
the document has existed without anything noticing. A caps-collapse that is
only a fix can be undone by the next person who adds a slice to make a page
fit — which is exactly how `[:4]` got there.

So this asserts the invariant rather than the change: whatever the set size,
the analysis note, `total_comps`, the chart, and the rendered document all
say the same number, and both ends of the range are visible. Any new cap
anywhere in the chain fails it, whichever file it is added to.
"""
import os
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tests"))

os.environ.setdefault("DATABASE_URL", "postgresql://fake/fake")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")

from worker.consumer_report_data import build_consumer_report_data  # noqa: E402
from worker.property_builder import (  # noqa: E402
    COMP_SET_MAX,
    THEME_TEMPLATES,
    PropertyReportBuilder,
)

from test_property_production_render import COMPS, report_data  # noqa: E402

THEMES = sorted(THEME_TEMPLATES)

from _template_chain import SHARED_THEMES, chain, is_shared  # noqa: E402


def _text(html: str) -> str:
    """Rendered text, tags out and whitespace collapsed.

    The counts this file asserts are sentences a reader sees ("Each sale 15"),
    and the shared architecture splits them across sibling elements. Matching
    the markup would be matching one architecture's spelling of the number.
    """
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html)).strip()

TEMPLATES = ROOT / "src/worker/templates/property"

#: Distinctive enough to count in the rendered HTML without matching anything
#: the template writes itself.
ADDR = "{n} Quillback Terrace"


def comps(n, address=ADDR):
    out = []
    for i in range(n):
        c = dict(COMPS[i % len(COMPS)])
        c["address"] = address.format(n=7100 + i * 37)
        c["sale_price"] = 565_000 + i * 41_000
        c["price"] = c["sale_price"]
        out.append(c)
    return out


def rendered_addresses(html, n, address=ADDR):
    return sum(1 for i in range(n) if address.format(n=7100 + i * 37) in html)


def agent_html(theme, n):
    data = dict(report_data(theme))
    data["comparables"] = comps(n)
    return PropertyReportBuilder(data).render_html()


def consumer_html(theme, n):
    data = build_consumer_report_data(
        property_data={"address": "1358 5th Street", "requester_name": "Dana Ortiz"},
        prop_address="1358 5th Street", prop_city="La Verne", prop_state="CA",
        prop_zip="91750", comparables=comps(n))
    data["theme"] = theme
    return PropertyReportBuilder(data).render_html(), data


# ── THE INVARIANT ───────────────────────────────────────────────────────────

SIZES = (1, 2, 3, 4, 5, 8, COMP_SET_MAX)


@pytest.mark.parametrize("theme", THEMES)
@pytest.mark.parametrize("n", SIZES)
def test_every_count_in_the_document_is_the_same_count(theme, n):
    """The one assertion D-159 is about, at seven set sizes and five themes.

    `n >= 3` is where the note states a number; below that `_analysis_columns`
    says "one comparable sale" or "two comparable sales" in words, which is
    checked separately.
    """
    html = agent_html(theme, n)
    shown = rendered_addresses(html, n)
    assert shown == n, (
        f"{theme}, {n} comps supplied: {shown} appear in the document. The "
        f"range and the analysis table are computed over all {n}; a reader "
        f"can only check the {shown} they can see."
    )

    # THE COUNT THE DOCUMENT STATES, wherever this architecture states it.
    #
    # The nine-page themes print "every one of the N appears" in the analysis
    # note. Design's six-page architecture has no analysis note — it heads the
    # per-sale list "Each sale · N" and the range panel "Range supported by N
    # closed sales". Different sentence, same assertion: a number the reader
    # can check against what they can see, and D-159 is about those two
    # disagreeing.
    #
    # Re-pointed rather than skipped for the shared themes, because "the
    # document no longer states a count" would be a regression and this is
    # the only thing that would notice.
    if theme in SHARED_THEMES:
        stated = re.search(r"Each sale · (\d+)", _text(html))
        assert stated, f"{theme}: the per-sale list lost its count"
        assert int(stated.group(1)) == n, (
            f"{theme}: 'Each sale' claims {stated.group(1)} and {n} were supplied"
        )
    elif n >= 3:
        note = re.search(r"every one of the (\d+) appears", html)
        assert note, f"{theme}: the analysis note lost its count"
        assert int(note.group(1)) == n, (
            f"{theme}: the note claims {note.group(1)} and {n} were supplied"
        )


@pytest.mark.parametrize("theme", SHARED_THEMES)
@pytest.mark.parametrize("n", SIZES)
def test_the_shared_architecture_states_the_count_in_two_places_and_they_agree(theme, n):
    """The badge's replacement, and there are two of them.

    Design's architecture drops the Total Comps badge and states the count
    twice instead: "Each sale · N" over the per-sale list, and "N sales
    within R" beside the confidence pill. Two statements of one number is the
    shape D-159 is about, so they are asserted against each other and against
    the supplied set.

    The RANGE panel's count is deliberately NOT asserted equal to these: it
    says "Range supported by N closed sales" and is the closed-only subset,
    which is a different and smaller number on purpose.
    """
    text = _text(agent_html(theme, n))
    each = re.search(r"Each sale · (\d+)", text)
    header = re.search(r"(\d+) sales within", text)
    assert each and header, (
        f"{theme}: the document states the comp count in "
        f"{sum(1 for m in (each, header) if m)} of 2 places"
    )
    assert int(each.group(1)) == n == int(header.group(1)), (
        f"{theme}: 'Each sale' says {each.group(1)}, the header says "
        f"{header.group(1)}, {n} were supplied"
    )


@pytest.mark.parametrize("theme", THEMES)
def test_both_ends_of_the_range_are_visible_in_the_document(theme):
    """The defect in one line.

    The range is `min(prices)`..`max(prices)` over the whole set. With the
    cards page holding four of fifteen, the top of the range was a number
    with no evidence anywhere in the document — the page whose only purpose
    is letting a seller check it showed them the bottom 21%.
    """
    rows = comps(COMP_SET_MAX)
    html = agent_html(theme, COMP_SET_MAX)
    lo, hi = min(c["sale_price"] for c in rows), max(c["sale_price"] for c in rows)
    for label, value in (("low", lo), ("high", hi)):
        assert f"{value:,}" in html, (
            f"{theme}: the {label} end of the range (${value:,}) appears "
            f"nowhere in the document the range is printed in"
        )


@pytest.mark.parametrize("theme", SHARED_THEMES)
def test_the_shared_architecture_draws_one_bar_per_comp(theme):
    """The chart's replacement, and it is a stronger assertion than the one it
    replaces.

    The nine-page themes draw a four-bar chart over a table summarising
    fifteen comps — D-159's original finding, fixed by making the chart draw
    the set. Design's architecture has no chart on the comparables page; page
    4 lists EVERY comp as its own bar, so the assertion is exact rather than
    "the chart draws as many as the table counts".
    """
    for n in (1, 4, 8, COMP_SET_MAX):
        html = agent_html(theme, n)
        bars = html.count('class="bar-fill"')
        assert bars == n, (
            f"{theme}: {n} comps supplied, {bars} bars drawn on the range page"
        )


# ── the continuation page exists exactly when there is a continuation ───────

# ── ONE NUMBER, ONE PLACE ───────────────────────────────────────────────────

#: Every file that renders, across every theme — entry files and the shared
#: architecture they include. Was the five entry files; a theme on the shared
#: architecture keeps `comparables[:N]` out of reach of a gate that reads only
#: its thirty-four-line entry file.
LIVE_TEMPLATES = {p for t in THEME_TEMPLATES for p in chain(t)}


#: The one directory a live template may reach into.
SHARED_DIR = "_v2"

#: The directory it may not. `templates/property/_base/` is D-131's dead tree —
#: 5,570 lines that
#: render nowhere and that three separate pieces of work read as if they did.
DEAD_DIR = "_base"


def test_a_live_template_reaches_only_the_shared_architecture():
    """THE BOUNDARY, STATED OUT LOUD, BECAUSE AN UNSTATED ONE READS AS NONE.

    CHANGED DELIBERATELY ON 2026-10-06, which is what the old version of this
    test asked for by name ("if a live template ever starts extending or
    importing one of the others, this fails and the gate's scope has to grow
    with it") and what Design's README asks for by name too.

    It used to forbid `extends`, `import`, `include` and `from` outright. That
    was never the property — it was a proxy for it. `templates/property/`
    holds TWO template trees and the one under `property/_base/` renders nowhere
    (NOT `market/_base/`, which is the base of every market report — the two
    builders resolve the same name against different directories), so
    what matters is which tree a live file reaches. Design's package
    introduces a THIRD thing, `_v2/report.jinja2`, which is neither: it is the
    document, shared by every theme on the new architecture, and it is
    rendered.

    So the gate is NARROWED, not dropped:

      * a live template may reach `_v2/`
      * a live template may NOT reach `_base/`, directly or transitively
      * every file it does reach must exist and must be under
        `templates/property/`

    The scope of the comp gate below grows with it automatically, because it
    now reads each theme's whole chain rather than its entry file.

    The dead set still carries `comparables[:4]` in seven places. Deleting it
    is its own change and not this one; what must not happen is the gate
    quietly covering less than it claims.
    """
    for theme in THEMES:
        files = chain(theme)
        names = [str(f.relative_to(TEMPLATES)) for f in files]
        for name in names:
            assert not name.startswith(DEAD_DIR + "/"), (
                f"{theme} reaches {name}, which is in the tree that renders "
                f"nowhere (D-131). Every cost that tree has charged came from "
                f"someone reading it as live; a live template reaching into "
                f"it makes that reading correct."
            )
        for name in names[1:]:
            assert name.startswith(SHARED_DIR + "/"), (
                f"{theme} reaches {name}, which is neither its own entry file "
                f"nor under {SHARED_DIR}/. If this is a new shared file, add "
                f"its directory to SHARED_DIR deliberately — one more place a "
                f"page's markup can live is one more place to look for it."
            )


def test_the_shared_architecture_is_reached_by_something():
    """Otherwise the test above passes on a `_v2/` nothing renders.

    A shared file no theme includes is the dead tree being recreated, and the
    whole of D-131 is that nobody noticed the first one.
    """
    reached = {
        str(f.relative_to(TEMPLATES))
        for theme in THEMES for f in chain(theme)[1:]
    }
    shared = {
        str(f.relative_to(TEMPLATES))
        for f in (TEMPLATES / SHARED_DIR).rglob("*.jinja2")
    }
    assert shared, f"{SHARED_DIR}/ holds no templates"
    orphans = sorted(shared - reached)
    assert not orphans, (
        f"{orphans} are in {SHARED_DIR}/ and no theme reaches them. Either "
        f"wire them up or delete them — a shared file nothing includes is "
        f"D-131's dead tree starting again."
    )


def _jinja_comp_slices(src: str):
    """`comparables[:N]` with a literal N, found by PARSING.

    Grepping found this file's own prose about the defect — twice, in the
    template comment explaining the fix and in the Python comment recording
    what the cap used to be. Eighth time that trap has fired in this project
    and the first two caught before they shipped. §0.6: a substring is not a
    construct.
    """
    from jinja2 import Environment, nodes
    out = []
    for n in Environment().parse(src).find_all(nodes.Getitem):
        target = getattr(n.node, "name", None)
        if target != "comparables":
            continue
        sl = n.arg
        if isinstance(sl, nodes.Slice) and isinstance(sl.stop, nodes.Const):
            out.append((n.lineno, sl.stop.value))
    return out


def test_no_live_template_caps_the_comparables_with_a_literal():
    """`[:4]` in twenty-four loops is how the document came to disagree with
    itself. The split lives in the context now; a literal is a second
    opinion about it."""
    offenders = []
    for path in sorted(LIVE_TEMPLATES):
        for lineno, stop in _jinja_comp_slices(path.read_text(encoding="utf-8")):
            offenders.append(f"{path.name}:{lineno}  comparables[:{stop}]")
    assert not offenders, (
        "a template caps the comparable set with a literal:\n  "
        + "\n  ".join(offenders)
        + "\nUse `comparables[:_cards]`, which comes from "
          "`cards_per_comparables_page`, so the cards page and the "
          "continuation page cannot disagree about the split."
    )


def test_no_python_caps_the_comparables_with_a_second_literal():
    """Also parsed, for the same reason — the first version of this test was
    answered by the comment in `consumer_report_data.py` that records what
    the cap used to be."""
    import ast
    srcs = [ROOT / "src/worker/property_builder.py",
            ROOT / "src/worker/consumer_report_data.py",
            ROOT / "src/worker/tasks.py"]
    names = {"comparables", "raw_comps", "comps"}
    offenders = []
    for path in srcs:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Subscript) or not isinstance(node.slice, ast.Slice):
                continue
            base = node.value
            if getattr(base, "id", None) not in names:
                continue
            upper = node.slice.upper
            if isinstance(upper, ast.Constant) and isinstance(upper.value, int):
                offenders.append(f"{path.name}:{node.lineno}  {base.id}[:{upper.value}]")
    assert not offenders, (
        "the comparable set is capped by a literal:\n  " + "\n  ".join(offenders)
        + "\nSize it once, in `property_builder.COMP_SET_MAX`."
    )


def test_the_api_and_the_worker_agree_on_the_set_size():
    """A cross-deployment constant has no way to be one number except this.

    `apps/api` cannot import `apps/worker` and vice versa — separate
    deployments — so `ComparablesRequest.limit` carries the same number and
    this parses both files. Change one and it names the other.
    """
    api = (REPO / "apps/api/src/api/routes/property.py").read_text(encoding="utf-8")
    m = re.search(r"limit:\s*int\s*=\s*Field\(default=(\d+)", api)
    assert m, "ComparablesRequest.limit is no longer a Field with a default"
    assert int(m.group(1)) == COMP_SET_MAX, (
        f"the API returns up to {m.group(1)} comparables and the worker sizes "
        f"the set at {COMP_SET_MAX}. Whichever is smaller is the real cap, and "
        f"nothing downstream knows which. routes/property.py:ComparablesRequest"
    )


# ── the consumer path is not thinner (the fifth time) ───────────────────────

@pytest.mark.parametrize("theme", THEMES)
def test_the_consumer_report_carries_the_same_set_as_the_agent_report(theme):
    """D-138, D-139, D-140, D-141 and now D-159 — five findings of this path
    carrying less than the agent path, four of them accidental and none with
    a recorded reason. D-157 is the one deliberate divergence and it is about
    the owner of record, not the evidence."""
    html, data = consumer_html(theme, COMP_SET_MAX)
    assert len(data["comparables"]) == COMP_SET_MAX, (
        f"the consumer builder forwards {len(data['comparables'])} of "
        f"{COMP_SET_MAX} comparables"
    )
    assert rendered_addresses(html, COMP_SET_MAX) == COMP_SET_MAX, (
        f"{theme}: the consumer report shows fewer comps than it was given"
    )


def test_every_theme_is_on_the_shared_architecture():
    """The consolidation, held. A theme whose entry file stopped including
    `_v2/report.jinja2` would render a self-contained document again — and
    every gate written against the shared architecture would skip it, because
    they parametrize over `SHARED_THEMES`, which is derived."""
    assert SHARED_THEMES == THEMES, (
        f"self-contained again: {sorted(set(THEMES) - set(SHARED_THEMES))}")
    for theme in THEMES:
        assert is_shared(theme), theme

