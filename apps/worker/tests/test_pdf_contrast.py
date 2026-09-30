"""The contrast gate for the market and property PDFs.

WHY THIS FILE EXISTS
--------------------
`test_email_contrast.py` has been green for weeks and walks only the email
templates. `docs/TEST_DURABILITY.md` named that as the one gate that would keep
passing while covering nothing, and measuring it proved the point harder than
predicted: these documents had never been audited at all, and the first pass
found **1,387 text runs below their WCAG threshold, 94 of them invisible**
(`docs/CONTRAST_AUDIT_PDF_2026-09-29.md`).

A gate at 4.5:1 would therefore fail on its first commit, so this is a
RATCHET: every failing (document family, selector, foreground, background)
combination that exists today is recorded in `pdf_contrast_baseline.txt`, and
the build fails on a combination that is not. New unreadable text cannot ship;
the existing 1,387 are a debt with a number on it rather than a surprise.

WHAT IT IS KEYED ON, AND WHY NOT A FILE PATH
---------------------------------------------
`scripts/template_color_baseline.txt` keys its ratchet on file paths, which is
its weakness: a template replacement invalidates every line and the "may only
shrink" rule then constrains nothing. This keys on
**(family, selector, foreground, background)**, none of which is a path. A
replacement template set inherits the entries whose selectors it reuses and
gets a failure for every new pairing it introduces — which is the behaviour
that survives Claude Design's rewrite.

It deliberately does NOT record a count. The number of runs is a function of
how many rows the fixture has; the colour pairing is the defect.

WHY A BROWSER, AND WHY A MISSING BROWSER IS A FAILURE RATHER THAN A SKIP
-------------------------------------------------------------------------
PDFShift renders these with Chromium, so `getComputedStyle` is the ground
truth. Three separate resolution bugs in the first version of the walker were
caught only by a browser disagreeing with a reading of the CSS — see the
script's header.

A gate that skips when its tooling is absent is a gate that goes quiet exactly
when nobody is watching, which is the failure this whole file is a response to.
So: `PDF_CONTRAST_REQUIRE_BROWSER=1` (set in CI) turns a missing browser into a
failure. Locally, without it, the measurement skips and says so.
"""
import importlib.util
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "apps/worker/src"))

BASELINE = Path(__file__).parent / "pdf_contrast_baseline.txt"
REQUIRE = os.environ.get("PDF_CONTRAST_REQUIRE_BROWSER") == "1"


def _corpus():
    """The documents. `measure_pdf_contrast.py` still builds them — it is the
    corpus definition, 30 market and 30 property renders across six brands."""
    spec = importlib.util.spec_from_file_location(
        "_measure_pdf_contrast", ROOT / "scripts/measure_pdf_contrast.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _measurer():
    """THE MEASUREMENT, AND IT IS NO LONGER THE WALKER — D-130.

    `measure_pdf_contrast.py` resolves "what is painted behind this text"
    from the `elementsFromPoint` stack expanded with DOM ancestors. Measured
    against pixel truth over the property surface it produced **22 false
    1.00:1 readings in 1,965 runs and zero misses**, by two mechanisms: an
    absolutely-positioned child attributed to a parent whose painted box it
    has escaped, and `pointer-events:none` hiding an element from hit-testing
    so its own background is never considered.

    That is the FOURTH confident wrong reading from that resolver, and one of
    the two was introduced by the fix for the third. The pattern is not a bug
    to find once: every fix was correct for the case it was written against
    and wrong for a case it did not have.

    So the gate stops hit-testing. `measure_contrast_by_pixel.py` renders each
    document twice — once to collect every text run's rect, once with the
    glyphs blanked — and reads the pixel at each rect. That pixel IS the
    backdrop, whatever painted it: no chain, no ancestors, no assumption about
    paint order, nothing to be wrong about. It costs one extra screenshot per
    document.

    The walker stays in the tree. It is the comparison that established this,
    and a second opinion is worth keeping — but it is not what the build is
    read through any more.
    """
    spec = importlib.util.spec_from_file_location(
        "_measure_contrast_by_pixel", ROOT / "scripts/measure_contrast_by_pixel.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _browser_available(measure):
    """None when the measurement can run, else why not.

    PROBED BY LAUNCHING, NOT BY LOOKING FOR A FILE. The first version checked
    for a chromium under PLAYWRIGHT_BROWSERS_PATH, which is one machine's
    convention: CI installs to ~/.cache/ms-playwright and Playwright resolves
    it unaided, so the gate failed on a runner that had a working browser.
    Asking a heuristic where the browser is, instead of asking whether it
    starts, is the same mistake the walker itself made three times.

    The probe runs the exact launch the measurement will run, with the exact
    path it will pass, so a pass here means the real thing works.
    """
    if shutil.which("node") is None:
        return "node is not installed"
    exe = measure.find_chromium()
    # No backslash escapes in this string. The first version trimmed the
    # error with `String(e).split('\\n')[0]`, and Python turned that into a
    # real newline inside a single-quoted JS string — a SyntaxError, so node
    # exited 1 and the probe reported "the browser will not launch" on a
    # machine whose browser launches fine. The trimming happens in Python
    # below, where there is no second layer of quoting to get wrong.
    script = (
        "const {chromium} = require('playwright');"
        "const exe = process.argv[1] || null;"
        "chromium.launch(exe ? {executablePath: exe} : {})"
        "  .then(b => b.close()).then(() => process.exit(0))"
        "  .catch(e => { console.error(e.message || String(e)); process.exit(1); });"
    )
    probe = subprocess.run(["node", "-e", script, exe], cwd=str(ROOT),
                           capture_output=True, text=True, timeout=180)
    if probe.returncode != 0:
        # The FIRST meaningful line. Taking the last one reported node's own
        # version banner ("Node.js v22.22.2") as the reason the browser would
        # not start, which is a diagnosis that sends the reader nowhere.
        lines = [ln.strip() for ln in (probe.stderr or probe.stdout or "").splitlines()
                 if ln.strip() and not ln.startswith("Node.js v")]
        return f"chromium will not launch: {lines[0] if lines else 'no output'}"
    return None


def key(row):
    """What the baseline records. No path, no count, no brand name.

    The brand is already in the colours — `#ffffff on #84cc16` IS the lime
    case — so naming it again would make the entry brittle against a renamed
    fixture without making it more specific.
    """
    # `fg_hex`/`bg_hex`, not `fg`/`bg`: the pixel measurer reports the raw CSS
    # colour (`rgb(255, 255, 255)`) and the resolved hex separately, and the
    # hex is what the baseline has always recorded. A translucent foreground
    # is flattened over its own backdrop pixel before hexing, which the walker
    # could not do at all.
    family = row["doc"].rsplit("__", 1)[0]
    return (family, row["selector"], row["fg_hex"], row["bg_hex"])


#: How far two colours may differ and still count as the same entry. (D-153)
#:
#: THE KEY USED TO BE AN EXACT HEX, AND THE BACKDROP IS SAMPLED FROM THE
#: RENDERED PIXEL — so over a gradient it is "wherever this run's text happened
#: to sit", and any layout change rewrites it. Demonstrated end to end on a run
#: this gate actually records: modern's `div.cover-city` at 4.01:1, below its
#: 4.5 threshold and on the baseline, moved `#3b4053` -> `#3c4155` when the
#: cover was given 120px of padding and NO colour was touched. Distance 4, and
#: an exact-hex key treats 4 the same as 300 — a new pairing, reported, on a
#: build where nothing about contrast changed.
#:
#: TWELVE, AND THE FIRST ANSWER WAS 48, WHICH WAS WRONG.
#:
#: 48 came from grouping the TEN SINGLE-BRAND production renders and finding a
#: gap between 37 and 131. Then it was applied to THIS corpus — sixty
#: documents across SIX brand colours — which contains a phenomenon those ten
#: do not. Measured here, the closest pairs of distinct baseline entries are:
#:
#:      3   elegant  span                  #57860e  vs  #58880e   <- gradient churn
#:      9   teal     h2.h                  #3b4569  vs  #3e486c   <- gradient churn
#:     18   elegant  div.num               #f2faf9  vs  #faf7f2   <- mint vs cream page
#:     30   modern   div.brand             #f1f5f9  vs  #ffffff   <- panel vs page
#:     41   bold     div.cover-label       #0d9488  vs  #0e7490   <- TWO DIFFERENT BRANDS
#:
#: 48 collapses the two brands. The corpus renders six on purpose, so merging
#: them is not a tolerable rounding — it is the gate losing the distinction it
#: was built to make. 14 of 178 entries collapse at 48; 3 at 12, and those
#: three are the 3-apart and 9-apart pairs, which ARE one finding sampled at
#: two points on one gradient.
#:
#: So the bound that matters is not a gap between two tidy populations. It is:
#: above the churn (observed 2, 3, 4) with headroom, and below the smallest
#: distance between two backdrops that genuinely differ (18 here). Twelve.
#:
#: THE MISTAKE IS §0.6'S OWN, ONE ENTRY AFTER IT WAS WRITTEN: a derived number
#: is only as good as the input it was derived from, and 48 was derived from a
#: corpus that does not contain brands.
#:
#: Re-derive rather than trusting: `scripts/measure_key_stability.py
#: --collisions` prints the closest distinct entries in THIS baseline, which
#: is the bound; `--nudge` prints the churn, which is the floor.
#:
#: NOT quantisation into buckets. Snapping each channel to a grid reproduces
#: the defect at every grid line — two colours 4 apart can straddle a boundary
#: and land in different buckets. A tolerance has no boundaries.
COLOUR_TOLERANCE = 12


def _rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def _near(a, b):
    try:
        return sum(abs(x - y) for x, y in zip(_rgb(a), _rgb(b))) <= COLOUR_TOLERANCE
    except (ValueError, IndexError):
        return a == b          # not a hex; fall back to equality


def same_entry(a, b):
    """Two keys naming the same (family, selector, colour pair).

    Family and selector must match exactly — they are names, not measurements.
    Only the two colours get the tolerance.
    """
    return a[0] == b[0] and a[1] == b[1] and _near(a[2], b[2]) and _near(a[3], b[3])


def new_findings(found, baseline):
    """Findings with no baseline entry within tolerance. The forward check."""
    return sorted(f for f in found if not any(same_entry(f, b) for b in baseline))


def stale_entries(found, baseline):
    """Baseline entries with no finding within tolerance. The reverse check.

    SAME PREDICATE AS `new_findings`, ON PURPOSE. Written as two expressions
    they drift, and the way they drift is the defect: a forward check with a
    tolerance and a reverse check on equality reports every absorbed entry as
    fixed, which is cleared by regenerating — the one move this file forbids.
    """
    return sorted(b for b in baseline if not any(same_entry(b, f) for f in found))


def read_baseline():
    if not BASELINE.exists():
        return set()
    out = set()
    for line in BASELINE.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        out.add(tuple(line.split("\t")))
    return out


def write_baseline(keys, stats):
    header = [
        "# Contrast failures in the market and property PDFs, as measured on",
        "# 2026-09-29. See docs/CONTRAST_AUDIT_PDF_2026-09-29.md for what they are.",
        "#",
        "# A RATCHET: this file may only shrink. A (family, selector, foreground,",
        "# background) combination that is not listed here fails the build.",
        "#",
        "# Keyed on the selector and the two colours, NOT on a file path, so a",
        "# replacement template set inherits the entries whose selectors it reuses",
        "# and earns a failure for every new pairing it introduces.",
        "#",
        "# THE COLOURS ARE MATCHED WITH A TOLERANCE, NOT BY EQUALITY (D-153). The",
        "# hexes below are exact and will not look like they are compared loosely;",
        f"# they are. Two colours within {COLOUR_TOLERANCE} (sum of |dR|+|dG|+|dB|) are the",
        "# same entry, in BOTH directions — a new finding matches an old line, and",
        "# an old line is only stale when nothing within tolerance still fails.",
        "#",
        "# Because the backdrop is sampled from the rendered pixel, over a gradient",
        "# it is 'wherever this run's text happened to sit'. Moving a line of text",
        "# changes it by a few units and an exact key would report a new pairing on",
        "# a build where no colour changed. Measured: modern's div.cover-city went",
        "# #3b4053 -> #3c4155 on a padding change alone.",
        "#",
        "# SO: IF THE GATE STAYS QUIET THROUGH A LAYOUT CHANGE, THAT IS DELIBERATE.",
        "# Re-derive the tolerance with scripts/measure_key_stability.py rather than",
        "# trusting it; it is only defensible while the two measured populations",
        "# stay separated, and a redesign moves them.",
        "#",
        "# Regenerate after FIXING something (never to clear a new failure):",
        "#     python3 -m pytest apps/worker/tests/test_pdf_contrast.py --regen-contrast-baseline",
        "#",
        f"# {stats}",
        "# Format: family<TAB>selector<TAB>foreground<TAB>background, sorted.",
        "",
    ]
    body = ["\t".join(k) for k in sorted(keys)]
    BASELINE.write_text("\n".join(header + body) + "\n", encoding="utf-8")


@pytest.fixture(scope="module")
def measured(request):
    measure = _measurer()
    why = _browser_available(measure)
    if why:
        if REQUIRE:
            pytest.fail(
                f"PDF_CONTRAST_REQUIRE_BROWSER=1 and the browser is unavailable: {why}. "
                f"This gate measures what Chromium paints; without it the suite would "
                f"report green on documents nothing looked at, which is the exact "
                f"failure it exists to prevent."
            )
        pytest.skip(f"{why} (set PDF_CONTRAST_REQUIRE_BROWSER=1 to make this a failure)")

    corpus = _corpus()
    docs = {}
    docs.update(corpus.market_documents())
    docs.update(corpus.property_documents())
    # `score` attaches fg_hex/bg_hex/ratio/needs; `doc` comes from the JS.
    return measure.score(measure.measure_docs(docs))


def test_no_new_unreadable_text_in_the_pdfs(measured, request):
    """
    THE RATCHET. A colour pairing not already on the board fails the build.

    If this fails, the fix is the template, not the baseline. The baseline is
    regenerated only after something has been FIXED, and its diff is what a
    reviewer reads — the same contract as golden/themes.json.
    """
    fails = [r for r in measured if r["ratio"] < r["needs"]]
    found = {key(r) for r in fails}
    baseline = read_baseline()

    if request.config.getoption("--regen-contrast-baseline", default=False):
        worst = min((r["ratio"] for r in fails), default=0)
        write_baseline(found, f"{len(fails)} failing runs, {len(found)} combinations, "
                              f"worst {worst:.2f}:1, of {len(measured)} runs measured.")
        pytest.skip(f"baseline regenerated: {len(found)} combinations")

    # D-153: matched with a tolerance, not by equality. `found - baseline`
    # would report a pairing whose backdrop moved 4 as brand new.
    new = new_findings(found, baseline)
    assert not new, (
        f"{len(new)} colour pairing(s) below their WCAG threshold that are not on the "
        f"baseline:\n  " + "\n  ".join(
            f"{ratio_of(measured, k):.2f}:1  {k[2]} on {k[3]}  {k[1]}  in {k[0]}"
            for k in new[:25]
        ) + "\n\nFix the template. Regenerate the baseline only after a fix, with "
            "--regen-contrast-baseline."
    )


def ratio_of(rows, k):
    return min(r["ratio"] for r in rows if key(r) == k)


def test_the_baseline_does_not_outlive_what_it_recorded(measured):
    """
    The other direction. An entry for a pairing that no longer fails means
    something was fixed and the board was not updated — and a baseline with
    dead entries is one nobody rechecks, which is how
    `template_color_baseline.txt` can silently stop constraining anything.

    Regenerating is one command and its diff is the evidence of the fix.
    """
    # D-153, AND IT MUST USE THE SAME TOLERANCE AS THE FORWARD CHECK, or this
    # gate creates the defect the tolerance removes: every entry the forward
    # check absorbs would read as "no longer fails" here, and clearing that
    # means regenerating — the one move this file forbids. §0.6, *a guard
    # asserting A implies B is half a guard*.
    fails = {key(r) for r in measured if r["ratio"] < r["needs"]}
    stale = stale_entries(fails, read_baseline())
    assert not stale, (
        f"{len(stale)} baseline entries no longer fail — something was fixed. "
        f"Regenerate with --regen-contrast-baseline so the diff records it:\n  "
        + "\n  ".join(f"{k[2]} on {k[3]}  {k[1]}  in {k[0]}" for k in stale[:25])
    )


def test_the_measurement_looked_at_something(measured):
    """
    A count of zero findings and a count of zero runs look identical from the
    outside, and this gate's whole reason for existing is that the email one
    was the second while reading as the first.
    """
    assert len(measured) > 8000, (
        f"only {len(measured)} text runs measured across the corpus — the walker "
        f"is broken, not the documents clean"
    )
    families = {r["doc"].rsplit("__", 1)[0] for r in measured}
    assert len([f for f in families if f.startswith("market")]) >= 8
    assert len([f for f in families if f.startswith("property")]) == 5


# ── D-153 · the key survives a layout change ───────────────────────────────

def test_a_backdrop_that_moved_a_few_units_is_the_same_entry():
    """The observed case, as an assertion.

    modern's `div.cover-city` is `#94a3b8` on `#3b4053` at 4.01:1 — below its
    4.5 threshold, so it is one of the 215 and one of this file's own lines.
    Given `.cover-left { padding-top: 120px }` and no colour change at all,
    the sampled backdrop became `#3c4155`. Distance 4.
    """
    before = ("property__modern", "div.cover-city", "#94a3b8", "#3b4053")
    after = ("property__modern", "div.cover-city", "#94a3b8", "#3c4155")
    assert same_entry(before, after)
    assert before != after, "if these are equal the test proves nothing"


def test_a_genuinely_different_backdrop_is_a_different_entry():
    """The tolerance must not swallow a real pairing, and the case that
    matters is not the obvious one.

    A coloured band against the page is 131 apart and no plausible tolerance
    reaches it. The one that nearly went wrong is two of the corpus's six
    BRAND colours — `#0d9488` and `#0e7490`, 41 apart — which the first
    recommended tolerance of 48 would have merged, losing exactly the
    distinction six brands are rendered to make.
    """
    teal_brand = ("property__bold", "div.cover-label", "#d69649", "#0d9488")
    cyan_brand = ("property__bold", "div.cover-label", "#d69649", "#0e7490")
    assert not same_entry(teal_brand, cyan_brand), (
        "two different brand colours collapsed into one baseline entry"
    )
    on_page = ("property__classic", "td", "#ffffff", "#ffffff")
    on_band = ("property__classic", "td", "#ffffff", "#4a90a4")
    assert not same_entry(on_page, on_band)


@pytest.mark.parametrize("field,other", [
    (0, "property__bold"),        # family
    (1, "div.brand"),             # selector
])
def test_the_tolerance_applies_to_colours_only(field, other):
    """Family and selector are names, not measurements. Exact match or
    nothing — two different elements that happen to share a colour pair are
    two findings."""
    a = ["property__modern", "div.cover-city", "#94a3b8", "#3b4053"]
    b = list(a)
    b[field] = other
    assert not same_entry(tuple(a), tuple(b))


def test_the_tolerance_is_the_one_the_measurement_supports():
    """A constant nobody re-derives is a constant that drifts from its reason.

    `scripts/measure_key_stability.py` reports the two populations and the gap
    between them. This asserts only that the value here sits inside the gap
    the entry records — 37 below, 131 above — so a future edit that nudges it
    out of that range fails here and sends the reader to the script.
    """
    assert 9 < COLOUR_TOLERANCE < 18, (
        f"{COLOUR_TOLERANCE} is outside the measured window. The floor is the "
        f"observed churn — 2, 3 and 4 from the nudge, and two baseline pairs "
        f"at 3 and 9 that are one finding sampled twice on a gradient. The "
        f"ceiling is the closest pair of backdrops that genuinely differ, 18. "
        f"Re-derive with scripts/measure_key_stability.py --collisions rather "
        f"than adjusting to taste."
    )


def test_both_directions_use_the_tolerance():
    """THE HALF-GUARD THIS WOULD OTHERWISE HAVE BEEN.

    The forward check asks "is this finding on the baseline"; the reverse
    asks "does this baseline line still fail". Give the first a tolerance and
    leave the second on equality and every absorbed entry reads as fixed —
    cleared by regenerating, the one move this file forbids.

    CONSTRUCTED, NOT OBSERVED, AND THE FIRST VERSION WAS NOT. It asserted
    over the real measurement that no entry was both matched and stale — and
    passed against a one-directional revert, because immediately after a
    regeneration the found set and the baseline are IDENTICAL, so nothing is
    absorbed by tolerance and there is nothing for the second direction to
    get wrong. A guard for a situation that cannot currently arise is a guard
    that passes for the wrong reason (§0.6). This builds the situation.
    """
    baseline = {("property__modern", "div.cover-city", "#94a3b8", "#3b4053")}
    # The same finding after a layout change: backdrop 4 away, nothing else.
    found = {("property__modern", "div.cover-city", "#94a3b8", "#3c4155")}

    assert not new_findings(found, baseline), (
        "the forward check reported a layout shift as a new colour pairing"
    )
    assert not stale_entries(found, baseline), (
        "the reverse check reported a still-failing entry as fixed — a "
        "one-directional tolerance, which is worse than none"
    )


def test_the_reverse_check_still_reports_a_genuinely_fixed_entry():
    """The other side of it: the tolerance must not make the staleness check
    toothless. An entry whose pairing is gone is still gone."""
    baseline = {("property__modern", "div.cover-city", "#94a3b8", "#3b4053")}
    assert stale_entries(set(), baseline) == sorted(baseline)
    far = {("property__modern", "div.cover-city", "#94a3b8", "#ffffff")}
    assert stale_entries(far, baseline) == sorted(baseline)
