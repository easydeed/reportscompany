"""
The consolidation's gate: a restructure must change nothing that renders.

Workstream C's remaining work replaces ~1,600 lines of Python f-strings with one
Jinja2 template assembled from named blocks. **Every design decision was already
made** — the colour roles in the email rebuild, the derivations in D-099 — so any
rendered value that changes during the restructure is a bug in the restructure,
not a decision.

Byte-diffing the HTML cannot express that: moving from f-strings to Jinja changes
indentation, attribute order and where the newlines fall, on every line. So the
baseline records what each document MEANS — its text runs with resolved
foreground and background, its links, its images, its custom properties, its
classes, its element counts — and this asserts those are unchanged.

WHAT IT DOES NOT CATCH, STATED SO THE GREEN IS NOT OVERREAD
-----------------------------------------------------------
Geometry. Two documents can agree on every fact here and lay out differently: a
`width="50%"` that became `width="33%"`, a padding change, a cell that moved
rows. `structure` catches gross shape changes and nothing finer. "The facts are
identical" is a weaker claim than "the render is identical" and the gap is
exactly where a restructure bug would hide — which is why the visual check
stays a human step.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _render_facts import diff, facts, load  # noqa: E402
from email_fixtures import CASES, render  # noqa: E402

GOLDEN = Path(__file__).resolve().parent / "golden" / "email_facts"


@pytest.mark.parametrize("name,brand,report_type", CASES)
def test_the_rendered_facts_are_unchanged(name, brand, report_type):
    path = GOLDEN / f"{name}.json"
    assert path.exists(), (
        f"no baseline for {name}. Run scripts/regen_email_facts.py — but only to "
        f"establish a baseline deliberately, never to make this pass."
    )
    d = diff(load(path), facts(render(report_type, brand)))
    assert not d, "\n".join(f"  {k}: {v}" for k, v in sorted(d.items()))


# ---------------------------------------------------------------------------
# The controls. §0.6 — a detector's silence means nothing until you have seen
# it speak, and this one's normal output is silence on ten parametrised cases.
# ---------------------------------------------------------------------------

def test_reformatting_alone_produces_no_diff():
    """
    POSITIVE CONTROL for the gate's PURPOSE. The restructure will reformat every
    line; if that registered as a change the gate would be unusable and someone
    would delete it.
    """
    a = '<table><tr><td style="background:#fff"><p style="color:#111">Hi</p></td></tr></table>'
    b = '<table>\n  <tr>\n    <td style="background:#fff">\n      <p style="color:#111">Hi</p>\n    </td>\n  </tr>\n</table>'
    assert diff(facts(a), facts(b)) == {}


@pytest.mark.parametrize("mutation,expect_key", [
    ('<p style="color:#ff0000">Hi</p>', "colours"),
    ('<p style="color:#111">Hello</p>', "text"),
    ('<p style="color:#111">Hi</p><a href="https://x/1">go</a>', "links"),
    ('<p style="color:#111">Hi</p><img src="https://x/i.png">', "images"),
    ('<p style="color:#111" class="mobile-stack">Hi</p>', "classes"),
    ('<p style="color:#111">Hi</p><p style="color:#111">Hi</p>', "structure"),
])
def test_a_real_change_is_reported(mutation, expect_key):
    """
    NEGATIVE CONTROL, one per fact set. A gate that only ever agrees is
    indistinguishable from a broken parser, and each fact set can break
    independently.
    """
    base = '<table><tr><td style="background:#fff"><p style="color:#111">Hi</p></td></tr></table>'
    changed = base.replace('<p style="color:#111">Hi</p>', mutation)
    d = diff(facts(base), facts(changed))
    assert expect_key in d, f"changing {expect_key} was not reported: {d}"


def test_a_changed_background_is_reported_even_though_the_text_is_the_same():
    """
    The background is RESOLVED from ancestors, so a restructure that re-nests an
    element into a different cell changes what the reader sees while every text
    run stays byte-identical. That is the restructure bug this gate exists for.
    """
    a = '<td style="background:#ffffff"><p style="color:#0b8378">Price</p></td>'
    b = '<td style="background:#f1f5f9"><p style="color:#0b8378">Price</p></td>'
    d = diff(facts(a), facts(b))
    assert "colours" in d and "text" not in d


# ---------------------------------------------------------------------------
# §06's other two acceptance criteria, as gates rather than intentions
# ---------------------------------------------------------------------------

#: Gmail clips at 102KB and hides everything after the cut — which on these
#: documents is the CTA and the unsubscribe link, so a clipped email is both
#: useless and non-compliant. §06 budgets 80KB for headroom.
GMAIL_CLIP_KB = 102
BUDGET_KB = 80


@pytest.mark.parametrize("name,brand,report_type", CASES)
def test_the_document_fits_the_size_budget(name, brand, report_type):
    kb = len(render(report_type, brand).encode("utf-8")) / 1024
    assert kb < BUDGET_KB, (
        f"{name} is {kb:.1f}KB against an {BUDGET_KB}KB budget "
        f"(Gmail clips at {GMAIL_CLIP_KB}KB and the CTA and unsubscribe link "
        f"are below the cut)"
    )


def test_the_size_budget_has_real_headroom_today():
    """
    Measured 23.9–34.5KB before the consolidation. Pinned as a range rather than
    a ceiling so that a restructure which doubles the document — inlining a block
    eight times instead of once, say — fails here even though it is still under
    80KB. A budget only consulted at its limit is not a budget.
    """
    sizes = {n: len(render(rt, b).encode("utf-8")) / 1024 for n, b, rt in CASES}
    worst = max(sizes.values())
    assert worst < 45, (
        f"the largest document is now {worst:.1f}KB, up from 34.5KB before the "
        f"consolidation: {sorted(((round(v, 1), k) for k, v in sizes.items()), reverse=True)[:3]}"
    )


def test_the_baseline_is_not_empty():
    """
    Ten files of facts. An empty baseline directory plus a working comparison
    looks identical to a working baseline plus a broken renderer.
    """
    files = sorted(GOLDEN.glob("*.json"))
    assert len(files) == len(CASES) == 10
    for f in files:
        data = load(f)
        assert len(data["text"]) > 40, f"{f.name} recorded only {len(data['text'])} text runs"
        assert data["links"], f"{f.name} recorded no links"
        assert data["colours"], f"{f.name} recorded no resolved colours"
        assert data["structure"]["table"] > 5, f"{f.name} recorded almost no structure"
        # `css_vars` is deliberately NOT asserted here: an email has no custom
        # properties, because mail clients have no reliable cascade and every
        # rule in these documents is inline. The field stays in the fact set
        # because the same instrument is the obvious one to point at the PDF
        # templates, where the custom properties are the whole colour system —
        # and because an empty field on both sides costs nothing.
        assert data["css_vars"] == [], (
            f"{f.name} grew custom properties — an email should have none, so "
            f"either the renderer changed or this assumption did"
        )
