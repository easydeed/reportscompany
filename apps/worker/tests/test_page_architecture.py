"""§7.1 variant A, guarded structurally — because nothing else can guard it.

The page architecture is four facts spread across three files, and every one of
them is invisible to a test that only looks at rendered output:

  * both PDFShift `start_at` values are 1,
  * the header slot carries the slim running head, not the masthead,
  * the masthead is body content,
  * each reservation equals what its document actually paints.

Break any of them and the HTML still renders, the contrast audit still passes
and the render diff still matches — the damage only appears in a PDF built by a
vendor this suite never calls. That is the behavioural/structural split again
(§0.6), and it is why these assertions read the source rather than the output.

THE START_AT PAIR IS THE ONE THAT MATTERS MOST. PDFShift accepts differing
values with a 200 and silently applies max(header, footer) to both, so a change
here does not fail loudly anywhere: it just removes the footer from page 1 of
every report. Measured four ways by scripts/probe_pdfshift_start_at.py (D-103).
"""

import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

TASKS = ROOT / "apps/worker/src/worker/tasks.py"
ENGINE = ROOT / "apps/worker/src/worker/pdf_engine.py"
MARKET = ROOT / "apps/worker/src/worker/templates/market/_base"

#: Measured at Letter width on 2026-09-24, and the reservations are set from
#: these. Pinned rather than read from the CSS: the point is that the two agree.
PAINTED_INCHES = {"running head": 0.417, "footer": 0.885}
RESERVED = {"header": 0.44, "footer": 0.89}


def test_both_start_at_values_are_one():
    src = TASKS.read_text(encoding="utf-8")
    call = re.search(r"pdf_path, html_url = render_pdf\((.*?)\n        \)", src, re.S)
    assert call, "the market-report render_pdf call moved; this gate needs its new anchor"
    body = call.group(1)
    for name in ("header_start_at", "footer_start_at"):
        match = re.search(rf"{name}\s*=\s*(\w+)", body)
        assert match, f"{name} is no longer passed explicitly"
        assert match.group(1) == "1", (
            f"{name}={match.group(1)}. Both must be 1. PDFShift does not reject a "
            f"mismatch — it returns 200 and applies max(header, footer) to both, "
            f"so page 1 silently loses its footer (D-103)."
        )


def test_the_header_slot_carries_the_running_head_and_not_the_masthead():
    head = (MARKET / "page_header.jinja2").read_text(encoding="utf-8")
    assert "running-head" in head
    assert "linear-gradient" not in head, (
        "the masthead's gradient is back in the header slot. That slot repeats "
        "on every page, and it cannot be made page-1-only — see D-103."
    )
    # Match MARKUP, not prose. The first version of this asserted the word
    # "masthead" was absent from the file, and failed on the comment explaining
    # why the masthead is not in it — the same false positive as grepping for a
    # CSS class name and hitting the stylesheet rule.
    assert 'class="masthead' not in head, (
        "masthead markup is in the header slot, which repeats on every page"
    )


def test_the_masthead_is_body_content():
    base = (MARKET / "base.jinja2").read_text(encoding="utf-8")
    macros = (MARKET / "macros.jinja2").read_text(encoding="utf-8")
    assert "{% macro report_masthead(" in macros
    assert "macros.report_masthead(" in base, (
        "nothing renders the masthead. It lives in the body now; if it is not "
        "called there, reports have no masthead at all."
    )


@pytest.mark.parametrize("slot,inches", sorted(RESERVED.items()))
def test_each_reservation_matches_what_its_document_paints(slot, inches):
    """The reservation is one-way: PDFShift clips at it rather than growing.

    Too small and content is cut; too large and every page gives up the
    difference — which is what 1.3in-for-1.165in cost before variant A.
    """
    src = ENGINE.read_text(encoding="utf-8")
    block = re.search(rf'base_payload\["{slot}"\] = \{{(.*?)\}}', src, re.S)
    assert block, f"the {slot} payload moved"
    height = re.search(r'"height":\s*"([\d.]+)in"', block.group(1))
    assert height, f"{slot} has no height"
    assert float(height.group(1)) == inches, (
        f"{slot} reserves {height.group(1)}in, this suite has {inches}in recorded. "
        f"If the document changed height, re-measure it and record the new value "
        f"here — the two numbers are one decision."
    )


def test_the_reservations_leave_a_small_one_way_allowance():
    """Reserved must exceed painted, and not by much.

    Under is a clip. Well over is the defect variant A was half about: 2.4in of
    every 11in page reserved for 1.946in of paint.
    """
    for painted, reserved in ((PAINTED_INCHES["running head"], RESERVED["header"]),
                              (PAINTED_INCHES["footer"], RESERVED["footer"])):
        assert reserved >= painted, f"{reserved}in reserved for {painted}in painted — clips"
        assert reserved - painted <= 0.03, (
            f"{reserved - painted:.3f}in of slack on every page; re-measure rather "
            f"than padding"
        )


def test_the_pdfshift_margins_are_zero_because_the_documents_carry_their_own():
    """A CSS padding cannot do this job — it applies once at the start of the
    flow, not after each page break — so the spacing lives inside the header and
    footer documents, inside their reserved heights."""
    src = ENGINE.read_text(encoding="utf-8")
    block = re.search(r"if header_html or footer_html:\s*margin = \{(.*?)\}", src, re.S)
    assert block
    for side in ("top", "bottom"):
        value = re.search(rf'"{side}":\s*"([^"]+)"', block.group(1))
        assert value and value.group(1) == "0", (
            f"margin.{side} is {value.group(1) if value else 'missing'}; it stacks "
            f"on top of the reservation and puts the two numbers back out of step"
        )
    assert '.rh-gap' in (MARKET / "page_header.jinja2").read_text(encoding="utf-8")
    assert '.pf-gap' in (MARKET / "page_footer.jinja2").read_text(encoding="utf-8")
