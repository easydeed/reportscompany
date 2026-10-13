"""Every chart §7.3 specifies, asserted as an ELEMENT on the kind that carries it.

THE FAILURE CLASS NOTHING ELSE ON THIS SURFACE COVERS. Every other gate asks
whether what renders is *correct* — the right colour, the right size, the right
page. None asks whether something the specification requires renders **at all**.
D-183 is the proof: when `inventory` moved to Design's `_v2` page, the pace
chart's producer, its note, its tests and its vendor fetch all survived, and the
only thing that vanished was the output. It was found because a test happened to
render the page, not because anything was looking for it. D-113 is the same
class in the other direction — a consumer reading `closed_history` that nothing
wrote, for months, in production.

THIS GATE HOLDS §7.3, NOT THE CURRENT RENDER. A registry built from what renders
today would ratify every gap it was built to catch: D-183's absence would become
the baseline, and the next one would too. So each entry cites the specification,
and a specified output that does not render is REPORTED — as a strict xfail
naming the defect that holds it — rather than recorded as normal.

WHAT MAKES AN ABSENCE LEGITIMATE, AND WHY THAT IS CHECKED AGAINST A DOCUMENT.
An absence may cite exactly one of two things, and the gate verifies both
against the file they name:

  * `defect=` a `D-NNN` that is **on the board**, or
  * `open_in_spec=` a sentence that appears **verbatim in the master plan**.

Neither can be written from this file alone. "We decided not to" is not an
option, which is the whole point: the cheap repair for a gate that goes red is
to tell it the absence is fine, and that repair is what would have made D-183
permanent.

FOUR PROPERTIES, EACH FROM SOMETHING THAT HAS ALREADY GONE WRONG HERE.

1. ELEMENT-ANCHORED, AND ENFORCED ON THE REGISTRY RATHER THAN REMEMBERED.
   `.band-chart`'s CSS rule is in the stylesheet of every page that shares it,
   so `'band-chart' in html` reports a band chart on every kind — which is how
   the first draft of the chart-scope measurement got its own table wrong. A CSS
   rule can contain neither `class="` nor `<`, so the gate asserts that of every
   marker it holds. The `<style>` strip below is belt to that braces: the strip
   relies on the next person remembering, the registry self-check does not.

2. BOTH DIRECTIONS. Present on every kind the spec names, **absent on every kind
   it does not** — which is what catches a chart appearing somewhere it was
   never designed for, and is the half D-183's surroundings lacked.

3. THE FIXTURE IS ASSERTED SEPARATELY, AND OUTSIDE THE XFAIL. The trend chart
   renders only when `closed_history` is in the report data: with the fixture
   from `test_market_layout_map.py`, which carries none, `market_snapshot`
   renders no chart and a gate built on it would report §7.3's first chart as
   missing on day one. The obvious repair — declare it absent — would encode the
   defect permanently. So `test_the_fixture_feeds_every_specified_output` proves
   the inputs are present and **never xfails**, which leaves the render tests
   with exactly one way to fail.

4. AN UNREGISTERED CHART IS AN ERROR, in both marks: the `<svg>` count per kind
   is derived from the registry, and the `chart` class tokens found in each body
   must be exactly the registered ones. A chart cannot be added to this surface
   without declaring where the specification puts it.

WHAT IT DOES NOT DO. It cannot read §7.3. The registry is hand-maintained against
the master plan, which makes it a second copy of a specification — the family
this project has filed most often. The mitigation is that it is a copy of four
entries, each carrying its source line, and that the alternative is no coverage
of the class at all. This gate is a pin, and pins go stale.
"""
import re
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "apps/worker/src"))
sys.path.insert(0, str(REPO / "scripts"))

from measure_market_pagination import _history, report_data  # noqa: E402
from worker.market_builder import ALL_REPORT_TYPES, MarketReportBuilder  # noqa: E402

MASTER_PLAN = REPO / "docs/plans/DELIVERY_SURFACES_MASTER_PLAN.md"
DEFECT_LIST = REPO / "docs/DEFECT_LIST.md"


#: §7.3's charts, one entry each, keyed by the name the plan uses.
#:
#: `kinds` is **what the specification names**, not what renders. `marker` is
#: the opening markup of the element, so it cannot match a stylesheet. `needs`
#: is what the producer reads out of the report data, so "absent" can never
#: mean "the fixture never fed it". Exactly one of `defect` / `open_in_spec`
#: is set when the output does not render, and both are checked against the
#: file they cite.
SPECIFIED_OUTPUT = {
    "median trend": {
        "source": "§7.3 — \"Two: the twelve-month median/pace trend and the "
                  "price-band distribution\"; built 2026-09-24 on market_snapshot",
        "kinds": frozenset({"market_snapshot"}),
        "needs": ("closed_history",),
        "marker": '<div class="trend-chart',
        "mark": "svg",
        "defect": None,
        "open_in_spec": None,
    },
    "pace trend": {
        # §7.3 asked for months of supply on `inventory`, established that it
        # cannot be built from an Active/Pending/Closed feed, and shipped the
        # knowable half in its place. That is the specified output here.
        "source": "§7.3 — \"What ships instead is the half that is knowable: "
                  "the sales pace\", on the inventory report",
        "kinds": frozenset({"inventory"}),
        "needs": ("closed_history",),
        "marker": '<div class="trend-chart',
        "mark": "svg",
        # Design's `_v2` page for `inventory` specifies no chart, so two
        # specifications disagree and the product owner has not ruled. The gate
        # holds §7.3 and reports the gap; it does not pick the winner.
        "defect": "D-183",
        "open_in_spec": None,
    },
    "band distribution": {
        "source": "§7.3 — \"the price-band distribution\"",
        "kinds": frozenset({"price_bands"}),
        "needs": ("price_bands",),
        # Design's `_v2` body draws a bar per band in CSS rather than the
        # inline SVG §7.3 built: same information, same comparison, same rules
        # on legends and labels, a different mark. Recorded here rather than
        # left for someone to discover as a mismatch.
        "marker": 'class="bbar',
        "mark": "css",
        "defect": None,
        "open_in_spec": None,
    },
    "DOM distribution": {
        "source": "§7.3 — the third chart, named in the plan's own prose",
        "kinds": frozenset({"closed"}),
        "needs": (),
        "marker": None,  # never built; there is no element to name
        "mark": None,
        "defect": None,
        "open_in_spec": "**`closed`'s DOM distribution is NOT built**, and "
                        "that is the §7.3 item that stays open.",
    },
}

#: Kinds a marker may legitimately appear on — the union across every output
#: that uses it. The two trend series share one element, so a per-entry
#: negative check would have each of them failing on the other's kind.
MARKER_OWNERS = {}
for _name, _spec in SPECIFIED_OUTPUT.items():
    if _spec["marker"]:
        MARKER_OWNERS.setdefault(_spec["marker"], set()).update(_spec["kinds"])

_STYLE = re.compile(r"<style[^>]*>.*?</style>", re.S)
_CHART_CLASS = re.compile(r'class="([^"]*\bchart\b[^"]*)"')


def body_of(report_type):
    """The document with every stylesheet removed.

    Belt to the registry's braces (property 1). Both are here because they fail
    differently: the strip is forgotten by whoever writes the next helper, the
    self-check is not.
    """
    data = report_data(report_type, 40)
    data["ai_insights"] = None
    data["closed_history"] = _history()
    return _STYLE.sub("", MarketReportBuilder(data).render_html())


def fixture_for(report_type):
    data = report_data(report_type, 40)
    data["closed_history"] = _history()
    return data


def rendered_cases():
    """(output, kind) for every output the specification places somewhere."""
    return sorted(
        (name, kind)
        for name, spec in SPECIFIED_OUTPUT.items()
        for kind in spec["kinds"]
    )


def absent_reason(spec):
    """The xfail reason, or None when the output is expected to render."""
    if spec["defect"]:
        return (f"{spec['defect']} — specified by {spec['source']} and not "
                f"rendering. An outstanding finding, not a baseline.")
    if spec["open_in_spec"]:
        return (f"specified by {spec['source']} and deliberately unbuilt: "
                f"{spec['open_in_spec']}")
    return None


# ── the registry's own shape, which nothing else can check ───────────────────

def test_every_marker_is_element_anchored():
    """A CSS rule cannot contain `class="` or `<`. A class name can be in both.

    This is the self-check that replaces remembering to strip the stylesheet,
    and it is the property the first chart-scope measurement failed: a
    class-name match reported a band chart on a kind that has never drawn one.
    """
    for name, spec in SPECIFIED_OUTPUT.items():
        marker = spec["marker"]
        if marker is None:
            continue
        assert 'class="' in marker or marker.startswith("<"), (
            f"{name}'s marker {marker!r} is a bare class name, so it matches "
            f"the stylesheet of every page that defines the rule. Anchor it to "
            f"the element: '<div class=\"...' or 'class=\"...'."
        )


def test_an_absence_cites_exactly_one_reason():
    for name, spec in SPECIFIED_OUTPUT.items():
        assert not (spec["defect"] and spec["open_in_spec"]), (
            f"{name} cites both a defect and the specification. One absence, "
            f"one reason — otherwise which one is resolved is unanswerable."
        )
        if spec["marker"] is None:
            assert absent_reason(spec), (
                f"{name} has no marker, so it cannot be asserted at all. An "
                f"output with nothing to match must say why it is absent."
            )


def entry_for(defect_id, board):
    """A defect's own section, from its heading to the next one."""
    start = board.index(f"### {defect_id} —")
    nxt = board.find("\n### D-", start)
    return board[start:] if nxt == -1 else board[start:nxt]


def test_a_cited_defect_is_on_the_board_and_names_this_file():
    """An absence cannot be declared from inside this file — BOTH DIRECTIONS.

    The repair that would have made D-183 permanent is one line here saying the
    absence is fine. Requiring a filed entry makes that repair cost a defect.

    The second half is `tests/test_xfail_defect_links.py`'s rule — *"reason ->
    defect ID, entry -> list of tests"* — applied to xfails that file cannot
    see. Its `SOURCES` is a hand-list and its convention is a static
    `_DNNN_GATED = pytest.mark.xfail` marker; the markers here are derived from
    the registry at collection time, so they match neither. Rather than add a
    second literal list of the kinds whose output is absent, the entry -> test
    half is checked here, where the registry already knows.
    """
    board = DEFECT_LIST.read_text(encoding="utf-8")
    for name, spec in SPECIFIED_OUTPUT.items():
        if not spec["defect"]:
            continue
        assert f"### {spec['defect']} —" in board, (
            f"{name} cites {spec['defect']}, which is not an entry in "
            f"docs/DEFECT_LIST.md. A specified output that does not render is "
            f"a defect on the board or it is not accounted for."
        )
        assert Path(__file__).name in entry_for(spec["defect"], board), (
            f"{spec['defect']} holds {name}'s absence and its entry does not "
            f"name {Path(__file__).name} — so whoever fixes it is not told "
            f"that an xfail here goes strict-green and breaks the build."
        )


def test_a_spec_stated_absence_is_quoted_from_the_spec():
    """`open_in_spec` is checked against the plan, verbatim.

    Otherwise it is the same "we decided not to" the defect citation closes,
    written in the specification's voice.
    """
    plan = MASTER_PLAN.read_text(encoding="utf-8")
    for name, spec in SPECIFIED_OUTPUT.items():
        if not spec["open_in_spec"]:
            continue
        assert spec["open_in_spec"] in plan, (
            f"{name} claims the plan leaves it open, and that sentence is not "
            f"in {MASTER_PLAN.name}. Quote the plan or cite a defect."
        )


def test_every_specified_output_names_a_live_report_type():
    for name, spec in SPECIFIED_OUTPUT.items():
        unknown = set(spec["kinds"]) - set(ALL_REPORT_TYPES)
        assert not unknown, f"{name} is placed on {unknown}, which are not report types"


# ── the fixture, proved outside the xfail (property 3) ───────────────────────

@pytest.mark.parametrize("name,kind", rendered_cases())
def test_the_fixture_feeds_every_specified_output(name, kind):
    """Never xfails, for any output, including the absent ones.

    If this lived inside the render test, an output's absence would be
    satisfied by a fixture that never fed its producer — and the two readings
    are opposites: one is a lost chart, the other is a test that proves
    nothing. `report_data()` in `test_market_layout_map.py` carries no
    `closed_history`, so this is not hypothetical.
    """
    data = fixture_for(kind)
    for key in SPECIFIED_OUTPUT[name]["needs"]:
        assert data.get(key), (
            f"the fixture for {kind} carries no {key!r}, which {name}'s "
            f"producer reads — so this file cannot tell a missing chart from a "
            f"missing input."
        )


# ── the two directions (properties 2 and 4) ──────────────────────────────────

@pytest.mark.parametrize("name,kind", rendered_cases())
def test_a_specified_output_renders_on_the_kind_that_specifies_it(name, kind, request):
    spec = SPECIFIED_OUTPUT[name]
    reason = absent_reason(spec)
    if reason:
        request.node.add_marker(pytest.mark.xfail(strict=True, reason=reason))
    assert spec["marker"], f"{name} has no marker to assert"
    assert spec["marker"] in body_of(kind), (
        f"{kind} does not render {name}, which {spec['source']} specifies. "
        f"This is a finding: either the output was lost, or the plan changed "
        f"and nobody said so."
    )


@pytest.mark.parametrize("report_type", sorted(ALL_REPORT_TYPES))
def test_no_output_renders_on_a_kind_that_does_not_specify_it(report_type):
    """The other direction — a chart somewhere it was never designed for.

    Keyed by MARKER, not by output: the median and pace series share one
    element, so asking "is the pace trend on market_snapshot" by its markup is
    unanswerable and asking it per output would fail on the other's kind.
    """
    body = body_of(report_type)
    for marker, owners in MARKER_OWNERS.items():
        if report_type in owners:
            continue
        assert marker not in body, (
            f"{report_type} renders {marker!r}, and no §7.3 entry places it "
            f"there. Either the specification gained a chart and this registry "
            f"did not, or a kind is drawing one by accident."
        )


@pytest.mark.parametrize("report_type", sorted(ALL_REPORT_TYPES))
def test_no_unregistered_chart_renders(report_type):
    """Property 4, in both marks.

    An inline SVG is counted; a CSS-mark chart is matched by its class token.
    Either way a chart that no registry entry claims is an error, so the next
    one cannot be added without declaring where the specification puts it.

    THE NET IS NOT THE SAME SIZE IN BOTH MARKS, and the difference is worth
    knowing rather than discovering. The SVG count is exact: any inline SVG
    this registry does not account for fails here. The class-token half only
    sees an element that calls itself a chart, so a CSS mark named like
    `price_bands`' own `bbar` — which is the one that already exists — is
    outside it and is covered only by its positive assertion above. A gate
    that claimed otherwise would be the same class of overstatement it exists
    to catch.
    """
    body = body_of(report_type)

    expected_svgs = sum(
        1 for spec in SPECIFIED_OUTPUT.values()
        if spec["mark"] == "svg" and report_type in spec["kinds"]
        and not absent_reason(spec)
    )
    assert body.count("<svg") == expected_svgs, (
        f"{report_type} renders {body.count('<svg')} inline SVG(s); the "
        f"registry accounts for {expected_svgs}. An unregistered chart, or one "
        f"this file still expects."
    )

    found = {t for value in _CHART_CLASS.findall(body) for t in value.split()
             if "chart" in t}
    claimed = {t for marker, owners in MARKER_OWNERS.items()
               if report_type in owners
               for t in re.findall(r'class="([^"]*)', marker)[0].split()}
    # A chart is an element FAMILY, not one element: `trend-chart-note` is the
    # caption §7.3 requires beside the mark ("a note states the sample"), and
    # demanding a registry entry per sibling would make the registry a copy of
    # the markup rather than of the specification.
    stray = sorted(
        t for t in found
        if not any(t == c or t.startswith(f"{c}-") for c in claimed)
    )
    assert not stray, (
        f"{report_type} renders chart element(s) {stray} that no §7.3 entry "
        f"claims."
    )
