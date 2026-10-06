"""
Which templates render, asserted per surface rather than per directory name.

WHAT THIS EXISTS TO PREVENT
---------------------------
D-131 recorded a dead template tree under `templates/property/`, and the
sentence it produced — repeated in nine places including the handover document
Design received — is **"everything in `_base/` renders nowhere"**. Unqualified.

There are two `_base/` directories:

    templates/property/_base/   dead: nothing reaches it
    templates/market/_base/     LIVE: `market/market.jinja2` is one line,
                                `{% extends '_base/base.jinja2' %}`, and that
                                base imports `_base/macros.jinja2`

Jinja resolves a template name against the loader's directory, and the two
builders give their loaders different ones, so the string `'_base/base.jinja2'`
names two different files depending on which surface is rendering. Acting on
"delete the `_base/` tree" would delete the base of every market report.

The entry was not wrong about `property/_base/`. It was written while looking
at `templates/property/`, and the sentence does not say so. **A classification
that omits its own scope reads as a classification of everything.** That entry
has been cited three times as a reason to delete.

HOW THIS ANSWERS IT
-------------------
By WALKING from the roots each builder actually renders — `THEME_TEMPLATES`
for the property reports, `market.jinja2` for the market ones — so "dead" is
derived per surface. `scripts/derive_template_reachability.py` is the
derivation; this module asserts the two things that must stay true of it.
"""
import importlib.util
import io
import json
import sys
from contextlib import redirect_stdout
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
DERIVE = REPO / "scripts/derive_template_reachability.py"
TEMPLATES = REPO / "apps/worker/src/worker/templates"

#: Documents and gates that make a claim about an unreachable tree. Each must
#: qualify which `_base/` it means.
CLAIMANTS = (
    "docs/DEFECT_LIST.md",
    "docs/CLAUDE_DESIGN_HANDOVER.md",
    "apps/worker/tests/_template_chain.py",
    "apps/worker/tests/test_one_comp_set.py",
    "apps/worker/tests/test_handover_numbers_are_current.py",
)


@pytest.fixture(scope="module")
def reach():
    spec = importlib.util.spec_from_file_location("_derive_reach", DERIVE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = module.main()
    assert rc == 0
    return json.loads(buf.getvalue())


def test_the_market_base_is_live(reach):
    """THE ONE THAT MATTERS, and it is the inverse of a dead-tree assertion.

    A gate that only ever says "this is dead" cannot catch a live file being
    classified dead. This says the market base IS reached, by name, so the
    sentence "everything in `_base/` renders nowhere" can never be true of the
    whole repository while it holds.
    """
    assert reach["market"]["_base_is_live"], (
        "nothing reaches templates/market/_base/ any more. Either the market "
        "report stopped rendering or it was restructured — and if it was "
        "restructured, every document saying `_base/` is dead needs rereading, "
        "because the only reason that sentence was dangerous was this file."
    )
    live = reach["market"]["live_files"]
    assert "_base/base.jinja2" in live and "market.jinja2" in live, (
        f"the market surface's live set is {live}"
    )


def test_the_property_base_is_dead(reach):
    """D-131's actual claim, scoped. Still true, and now derived."""
    dead = reach["property"]["dead_files"]
    assert "_base/base.jinja2" in dead and "_base/_macros.jinja2" in dead, (
        f"templates/property/_base/ is reachable after all: dead set is {dead}"
    )
    assert not reach["property"]["_base_is_live"]


@pytest.mark.parametrize("rel", CLAIMANTS)
def test_every_claim_about_a_dead_base_says_which_one(rel):
    """An unqualified `_base/` in a document that calls it dead.

    Nine of these existed, in the defect list, the handover sent to Design,
    and three gates. The handover is the one that cost something: a designer
    reading "everything in `_base/` renders nowhere" has no way to know there
    are two, and the market handoff in the same package is about the surface
    whose `_base/` is load-bearing.
    """
    import re
    text = (REPO / rel).read_text(encoding="utf-8")
    bad = []
    for n, line in enumerate(text.splitlines(), 1):
        if "_base/" not in line:
            continue
        # A mention is fine unless the same line calls it dead or unreachable.
        if not re.search(r"dead|render(s|ed)? nowhere|unreachable|do not read",
                         line, re.I):
            continue
        # Qualified if the surface is named on the line.
        if re.search(r"property/_base|market/_base|templates/property|"
                     r"property report|property template", line, re.I):
            continue
        # OR if the line is ABOUT the ambiguity rather than asserting it.
        #
        # This exemption exists because the gate failed on the two sentences
        # of D-131's own correction that state the rule — "there are two
        # `_base/` directories and only one of them is dead" and "no document
        # or gate calls `_base/` dead without saying which one". Both are
        # unqualified by necessity: naming one surface would make them false.
        #
        # Twelfth outing for §0.6's "a substring is not a construct", and the
        # third time in this project a gate has matched the prose explaining
        # the defect it searches for. The pattern is reliable enough to plan
        # for: when a fix documents a bug in place, the explanation lands in
        # the region the gate reads.
        if re.search(r"two `_base/`|which one|says which", line, re.I):
            continue
        bad.append((n, line.strip()[:110]))
    assert not bad, (
        f"{rel} calls `_base/` dead without saying which one:\n"
        + "\n".join(f"  :{n}  {l}" for n, l in bad)
        + "\n\ntemplates/market/_base/base.jinja2 is extended by "
          "market/market.jinja2 and is the base of every market report."
    )


def test_the_market_surface_has_no_dead_templates(reach):
    """And the roots that make that true are derived, not listed.

    The first version of the derivation followed Jinja edges only and reported
    `market/_base/page_header.jinja2` and `page_footer.jinja2` as dead. They
    are PDFShift's native header and footer, reached from Python:
    `MarketReportBuilder.render_page_header_html` calls
    `env.get_template("_base/page_header.jinja2")`.

    That is D-131's own mistake with the surfaces swapped, and it was one
    `git commit` from being filed as a new defect. So this asserts the
    corrected answer — zero dead market templates — which is only reachable if
    the `get_template` literals are being treated as roots.
    """
    assert reach["market"]["dead_files"] == [], (
        f"{reach['market']['dead_files']} look unreachable on the market "
        f"surface. Before filing anything: are they reached from PYTHON? "
        f"`get_template` literals are roots, and a template can be a root "
        f"with no Jinja referencing it."
    )


def test_the_get_template_literals_are_found_at_all(reach):
    """Otherwise the test above passes because the parser found nothing.

    A derived root set that comes back empty makes every reachability
    assertion weaker in a way that reads as stricter.
    """
    literals = reach["get_template_literals"]
    assert literals, (
        "no `get_template(\"...\")` literal was found anywhere in the worker, "
        "so the root set is whatever was hardcoded — which is the condition "
        "that produced the near-miss recorded on D-131."
    )
    assert "_base/page_header.jinja2" in literals, (
        f"the market running head is no longer loaded by name: {literals}"
    )
