"""
E15 / D-129 — nothing on a property report may be invisible.

WHAT E15 ACTUALLY WAS
---------------------
E15 filed the aerial page as carrying *no* page number. It carries one, in
white, on white. Every theme's aerial footer was written with
`style="color:#fff"` as though it sat on the dark map band — but `.aerial` is
a **light** page with a 6.5in map in the middle, and the footer is below it.

Measured by reading the rendered pixel, before:

    1.00:1  bold     div.num     #ffffff on #ffffff   '03'
    1.00:1  classic  div.num     #ffffff on #ffffff   '03'
    1.00:1  classic  div.brand   #ffffff on #ffffff
    1.11:1  elegant  div.num     #ffffff on #f3f3f3   '03'
    1.31:1  elegant  div.brand   #e8d5a3 on #f3f3f3
    1.07:1  teal     div.num     #ffffff on #f7f7f9   '02'   <- CONTENTS page

**The teal one is not on the aerial page**, which D-129's own table said it
was. Teal's contents is split — a dark gradient on the left, a light panel on
the right — and that footer is inside the panel. Teal's aerial footer is white
on `#555e7f` at 6.38:1 and is correctly white; so is modern's, on `#1a1f36` at
16.24:1. Two of the five themes were right and were left alone.

WHY THIS IS A FLOOR AND NOT PART OF THE RATCHET
------------------------------------------------
`test_pdf_contrast.py` is a ratchet: 203 failing colour combinations are
recorded in a baseline and only a NEW one fails the build. That is the right
shape for a 660-run debt nobody can clear in one pass, and the wrong shape for
this: a ratchet lets an invisible pairing be regenerated onto the baseline and
forgotten, which is how `03` in white on white survived long enough to be
filed as a missing number rather than an unreadable one.

So this floor is not baselined and has no exceptions. Text below 2:1 is not
low-contrast, it is **absent**, and a document that contains it is wrong in a
way no debt register should be able to absorb.

It reads the PIXEL rather than the DOM (`measure_contrast_by_pixel.py`)
because the walker over-reports at exactly this end of the scale: D-130
records 22 false 1.00:1 readings on this surface from absolutely-positioned
children and `pointer-events:none`. A floor built on the walker would fail on
text that is perfectly legible, and a gate whose every alarm is false gets
deleted.
"""
import json
import os
import sys
import tempfile
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(REPO / "scripts"))

os.environ.setdefault("DATABASE_URL", "postgresql://fake/fake")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")

from worker.property_builder import PropertyReportBuilder, THEME_TEMPLATES  # noqa: E402

from test_property_production_render import report_data  # noqa: E402

THEMES = sorted(THEME_TEMPLATES)

#: Below this, text is not hard to read — it is not there.
#:
#: 1.5 IS CHOSEN FROM THE MEASURED DISTRIBUTION, NOT FROM A STANDARD, and the
#: gap is what makes it meaningful. Across the five property renders the runs
#: sort into two populations with nothing between them:
#:
#:     absent   1.00, 1.00, 1.00, 1.07, 1.11, 1.31   <- the six E15 fixed
#:     ------   ( no run lands here )
#:     poor     1.90, 1.90, 1.90, …                  <- teal's #34d1c3 on white
#:
#: The 1.90 runs are teal's `h2.section-title` — every page heading in the
#: theme — plus its cover logo and two contact icons. They are legible: mint
#: on white at 34px is readable and unpleasant, which is a palette decision
#: (D-129's largest visible group) and belongs to the ratchet and to whoever
#: owns the brand. Setting this floor at 2.0 would have swept them in here,
#: where there is no baseline and no way to record a deliberate choice.
#:
#: If a future render closes that gap, this constant needs re-deriving rather
#: than nudging: the number is only honest while the two populations are
#: separate.
INVISIBLE = 1.5

#: Same contract as `test_pdf_contrast.py`. A gate that skips when its tooling
#: is missing goes quiet exactly when nobody is watching.
REQUIRE = os.environ.get("PDF_CONTRAST_REQUIRE_BROWSER") == "1"


@pytest.fixture(scope="module")
def measured():
    import measure_contrast_by_pixel as pixel

    if not pixel.find_chromium():
        msg = "no Chromium for the pixel measurement"
        if REQUIRE:
            pytest.fail(
                f"PDF_CONTRAST_REQUIRE_BROWSER=1 and {msg}. This gate measures "
                f"what Chromium paints; without it the suite reports green on "
                f"documents nothing looked at."
            )
        pytest.skip(f"{msg} (set PDF_CONTRAST_REQUIRE_BROWSER=1 to fail instead)")

    out = Path(tempfile.mkdtemp(prefix="e15-renders-"))
    for theme in THEMES:
        html = PropertyReportBuilder(report_data(theme)).render_html()
        (out / f"property__{theme}.html").write_text(html, encoding="utf-8")
    return pixel.score(pixel.measure(out))


def test_the_measurement_looked_at_something(measured):
    """Zero findings and zero runs look identical from outside."""
    assert len(measured) > 900, (
        f"only {len(measured)} text runs measured across five themes — the "
        f"measurement is broken, not the documents clean"
    )
    assert len({r["doc"] for r in measured}) == len(THEMES)


def test_no_text_is_invisible(measured):
    """THE FLOOR. No baseline, no exceptions, no ratchet."""
    invisible = sorted(
        (r for r in measured if r["ratio"] < INVISIBLE),
        key=lambda r: r["ratio"])
    assert not invisible, (
        f"{len(invisible)} text run(s) below {INVISIBLE}:1 — not low-contrast, "
        f"absent:\n  " + "\n  ".join(
            f"{r['ratio']:.2f}:1  {r['fg_hex']} on {r['bg_hex']}  "
            f"{r['selector']}  in {r['doc']}  {r['text'][:40]!r}"
            for r in invisible[:20]
        ) + "\n\nThis gate has no baseline. Fix the template."
    )


def test_every_page_number_is_legible(measured):
    """The specific thing E15 was about, asserted on its own.

    `div.num` is the page number. It is small text, so 4.5:1 is its threshold
    — and unlike the floor above, a page number failing WCAG while remaining
    visible is still a page number the reader cannot use.
    """
    bad = sorted(
        (r for r in measured
         if r["selector"].endswith("div.num") and r["text"].strip().isdigit()
         and r["ratio"] < r["needs"]),
        key=lambda r: r["ratio"])
    assert not bad, (
        f"{len(bad)} page number(s) below their threshold:\n  " + "\n  ".join(
            f"{r['ratio']:.2f}:1 (needs {r['needs']})  {r['fg_hex']} on "
            f"{r['bg_hex']}  in {r['doc']}  {r['text']!r}" for r in bad)
    )
