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


def _measurer():
    spec = importlib.util.spec_from_file_location(
        "_measure_pdf_contrast", ROOT / "scripts/measure_pdf_contrast.py")
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
    family = row["doc"].rsplit("__", 1)[0]
    return (family, row["selector"], row["fg"], row["bg"])


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

    docs = {}
    docs.update(measure.market_documents())
    docs.update(measure.property_documents())
    raw, _work = measure.measure(docs)
    rows = []
    for doc, payload in raw.items():
        for e in payload["runs"]:
            rows.append({**e, "doc": doc,
                         "ratio": measure.ratio(e["fg"], e["bg"]),
                         "needs": measure.required(e["size"], e["weight"])})
    return rows


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

    new = sorted(found - baseline)
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
    fails = {key(r) for r in measured if r["ratio"] < r["needs"]}
    stale = sorted(read_baseline() - fails)
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
