"""The narrative's copy budget and the box it has to fit are one decision (§7.2).

`ai_market_narrative.NARRATIVE_MAX_CHARS` and the `height` on
`.ai-narrative-text` in templates/market are two halves of the same number. The
budget exists because the box does not clip; the box is safe because the budget
holds. Split across a Python module and a CSS rule, they can drift apart
silently and the first sign would be a pushed-down table in a customer's PDF.

Most of this is browser-free and runs in CI. The one assertion that genuinely
needs a paginator — that a budget-length narrative renders inside four lines —
cannot, so it is `scripts/measure_market_pagination.py`'s territory and the
numbers it produced are recorded here as the pinned capacities below.
"""

import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from worker.ai_market_narrative import NARRATIVE_MAX_CHARS  # noqa: E402

MARKET_CSS = ROOT / "apps/worker/src/worker/templates/market/_base/base.jinja2"

#: Characters per line of `.ai-narrative-text`, measured by bisecting rendered
#: height at 14px/20.3px in the real column, with a long-word corpus.
CHARS_PER_LINE = 97

#: Page-1 listing capacity with the box fixed, measured at four narrative
#: lengths (none / 36 / 55 / 150 tokens) and identical across all four — which
#: is the property the fixed box exists to create. Recorded from
#: scripts/measure_market_pagination.py on 2026-09-24, 120 listings.
#:
#: `none` differs on purpose: no narrative means no box, so those reports hold
#: more. Two deterministic states, not a variable one.
PAGE_1_CAPACITY = {
    "new_listings_gallery": {"with_narrative": 6, "no_narrative": 6},
    "featured_listings": {"with_narrative": 6, "no_narrative": 6},
    "open_houses": {"with_narrative": 6, "no_narrative": 6},
    "market_snapshot": {"with_narrative": 3, "no_narrative": 3},
    "closed": {"with_narrative": 12, "no_narrative": 16},
    "inventory": {"with_narrative": 12, "no_narrative": 16},
    "price_bands": {"with_narrative": 3, "no_narrative": 5},
    "new_listings": {"with_narrative": 3, "no_narrative": 4},
}


def narrative_box_lines():
    """The line count in the CSS, read from the rule rather than assumed."""
    css = MARKET_CSS.read_text(encoding="utf-8")
    block = re.search(r"\.ai-narrative-text\s*\{(.*?)\}", css, re.S)
    assert block, ".ai-narrative-text rule not found in the market base template"
    height = re.search(r"height:\s*calc\(\s*(\d+)\s*\*\s*([\d.]+)em\s*\)", block.group(1))
    assert height, (
        "`.ai-narrative-text` has no `height: calc(N * Xem)`. The box must be a "
        "FIXED height — §7.2's whole decision is that page-1 capacity cannot "
        "depend on the length of model-generated prose."
    )
    return int(height.group(1)), float(height.group(2))


def test_the_narrative_box_is_a_fixed_number_of_lines():
    lines, em = narrative_box_lines()
    assert lines == 4, f"box is {lines} lines; the recorded decision is 4"
    assert em == 1.45, f"line-height multiplier is {em}, expected 1.45"


def test_the_copy_budget_fits_the_box_it_is_sized_for():
    """NARRATIVE_MAX_CHARS must not exceed what the box holds.

    The failure this prevents is a raised budget, or a shrunk box, landing
    without the other — which does not break anything visible in a test suite
    that never renders a page, and pushes the first table down in production.
    """
    lines, _ = narrative_box_lines()
    capacity = lines * CHARS_PER_LINE
    assert NARRATIVE_MAX_CHARS <= capacity, (
        f"budget is {NARRATIVE_MAX_CHARS} chars but a {lines}-line box holds "
        f"about {capacity} ({CHARS_PER_LINE}/line, measured). Raise the box or "
        f"lower the budget — they are one decision."
    )


def test_the_budget_is_not_so_small_the_box_is_mostly_empty():
    """The other direction: a budget far under the box wastes page 1.

    Without this, 'make the test pass' has a trivial answer — drop the budget to
    50 characters — which would satisfy the check above and give up three of the
    four lines this box costs every report.
    """
    lines, _ = narrative_box_lines()
    capacity = lines * CHARS_PER_LINE
    assert NARRATIVE_MAX_CHARS >= capacity * 0.9, (
        f"budget {NARRATIVE_MAX_CHARS} uses only "
        f"{NARRATIVE_MAX_CHARS / capacity:.0%} of a box that costs page 1 "
        f"{lines} lines on every report"
    )


def test_the_prompt_still_asks_for_the_length_the_box_is_sized_for():
    """Four lines is the measured height of three sentences. If the prompt's
    target moves, the box was sized against copy nobody is asking for."""
    src = (ROOT / "apps/worker/src/worker/ai_market_narrative.py").read_text(encoding="utf-8")
    assert "2-3 sentences" in src, (
        "the narrative prompt no longer asks for 2-3 sentences; the four-line "
        "box was measured against exactly that target (§7.2)"
    )


@pytest.mark.parametrize("report_type", sorted(PAGE_1_CAPACITY))
def test_every_report_type_has_a_recorded_page_1_capacity(report_type):
    """Pinned, the same way continuation pages are — these are the numbers
    §7.2's targets have to be written against, and they only mean anything
    while the box stays fixed."""
    entry = PAGE_1_CAPACITY[report_type]
    assert entry["with_narrative"] >= 0
    assert entry["no_narrative"] >= entry["with_narrative"], (
        f"{report_type}: a report WITHOUT a narrative cannot hold fewer "
        f"listings on page 1 than one with"
    )


def test_the_recorded_capacities_cover_every_report_type():
    from worker.market_builder import ALL_REPORT_TYPES
    assert set(PAGE_1_CAPACITY) == set(ALL_REPORT_TYPES)
