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


# ── the running head's content ───────────────────────────────────────────────

def _running_head(branding):
    from worker.market_builder import MarketReportBuilder
    data = {"report_type": "closed", "city": "Irvine", "lookback_days": 30,
            "listings": [], "metrics": {}, "counts": {"Closed": 40},
            "branding": branding}
    html = MarketReportBuilder(data).render_page_header_html()
    return re.search(r'<span class="rh-name">(.*?)</span>\s*</span>', html, re.S).group(1)


def test_the_running_head_carries_the_brand_not_the_report_title():
    """They used to say the same words 40px apart on page 1.

    On page 4 the useful thing is whose report this is; the report title is
    already on page 1's masthead, and the count in the band's right slot still
    names it in passing.
    """
    head = _running_head({"company_name": "Luxury Estates Realty",
                          "agent_name": "Jennifer Martinez", "primary_color": "#1B365D"})
    assert "Luxury Estates Realty" in head
    assert "Closed Sales" not in head, "the band is repeating the masthead's headline"


def test_the_running_head_falls_back_to_the_agent_then_to_the_title():
    """A band with nothing in it is worse than a repeat, so the fallback chain
    has to be exercised rather than assumed."""
    agent_only = _running_head({"agent_name": "Jennifer Martinez", "primary_color": "#1B365D"})
    assert "Jennifer Martinez" in agent_only

    neither = _running_head({"primary_color": "#1B365D"})
    assert "Closed Sales" in neither, "with no brand at all the band must not be empty"


# ── what still varies on page 1 ──────────────────────────────────────────────

def test_the_masthead_title_cannot_wrap():
    """The inverse of the test that used to live here, and the reason it flipped.

    This started as a PINNED DEFECT: it asserted the title was free to wrap and
    was to fail the day anyone bounded it, as the signal to re-measure
    PAGE_1_CAPACITY. That day arrived. The bound is now the thing to protect.

    What it protects: the title is the report type plus the CITY, and cities are
    unbounded. At 24px a long one wrapped to a second line and moved page 1 by
    0.300in, so page-1 capacity depended on which city an affiliate reported
    (D-102). One line in a fixed-height box removes that, for every city at
    once.
    """
    css = (MARKET / "base.jinja2").read_text(encoding="utf-8")
    for selector, expect_px in (("masthead-title", "29px"), ("masthead-subtitle", "17px")):
        rule = re.search(rf"\.{selector}\s*\{{(.*?)\}}", css, re.S)
        assert rule, f".{selector} rule not found"
        body = rule.group(1)
        # The DECLARATION, not the substring: `line-height:` contains `height:`,
        # which is what the first version of this file matched (§0.6).
        height = re.search(r"(?:^|;)\s*height\s*:\s*([\d.]+px)", body)
        assert height and height.group(1) == expect_px, (
            f".{selector} must have a fixed pixel height ({expect_px}); found "
            f"{height.group(1) if height else 'none'}. A height in `em` would "
            f"move with the title's step-down and put the variability back."
        )
        assert re.search(r"white-space\s*:\s*nowrap", body), f".{selector} can wrap"
        assert "text-overflow: ellipsis" in body, (
            f".{selector} clips without an ellipsis — cropping mid-word reads as "
            f"a rendering fault, where an ellipsis says a value was too long"
        )


def test_the_title_ladder_steps_down_for_a_long_city():
    """The ladder is what keeps a long title on one line rather than clipping it.

    Asserted at real city names, and at the worst case that reaches the ellipsis
    — not only at the fixture's "Irvine", which never leaves the top step.
    """
    from worker.market_builder import MarketReportBuilder
    b = MarketReportBuilder({"report_type": "closed", "city": "Irvine", "branding": {}})
    cases = [
        ("Closed Sales — Irvine", 24),
        ("Closed Sales — San Juan Capistrano", 18),
        ("Closed Sales — Rancho Santa Margarita", 18),
        ("New Listings Gallery — Rancho Santa Margarita and San Juan Capistrano", 14),
    ]
    for text, expected in cases:
        assert b._masthead_title_px(text) == expected, (
            f"{len(text)} chars -> {b._masthead_title_px(text)}px, expected {expected}"
        )


def test_the_ladder_never_returns_a_size_that_is_not_on_it():
    """A size off the ladder means the box was measured for a size nobody uses."""
    from worker.market_builder import MarketReportBuilder
    b = MarketReportBuilder({"report_type": "closed", "city": "Irvine", "branding": {}})
    allowed = {px for _, px in b._TITLE_LADDER} | {b._TITLE_MIN_PX}
    for n in range(0, 200):
        assert b._masthead_title_px("x" * n) in allowed


def test_the_ladder_is_monotonic():
    """A longer title can never be set larger than a shorter one."""
    from worker.market_builder import MarketReportBuilder
    b = MarketReportBuilder({"report_type": "closed", "city": "Irvine", "branding": {}})
    sizes = [b._masthead_title_px("x" * n) for n in range(0, 200)]
    assert sizes == sorted(sizes, reverse=True), "the ladder goes back up somewhere"
