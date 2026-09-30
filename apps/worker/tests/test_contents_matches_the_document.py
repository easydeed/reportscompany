"""
D-121 — the contents page is derived from the page set, and says the truth.

WHAT WAS WRONG, AND WHY IT WAS THREE THINGS AT ONCE
----------------------------------------------------
Every theme's contents page was a literal block of seven rows — ordinal, label
and page number all written out — with no reference to `page_set`. The page
footers were literals too. Two hand-maintained copies of a number that is a
property of the render, so they disagreed with the document and with each
other:

  * the contents advertised *Market Trends* at page 07 in reports that contain
    no Market Trends page, and *Executive Summary* at 02 in four of five;
  * every theme printed `03` on BOTH the overview page and the aerial page;
  * the labels had drifted from the pages — "Aerial Property View" over a page
    headed "Aerial View", "Estimated Value Range" over "Range of Sales".

`paginate()` now computes both from the final page set, after the conditional
pages are dropped, and each theme declares one `_titles` map that the page
heading and the contents row both read. The three failures had one cause and
have one fix.

WHY THESE ASSERTIONS AND NOT "THE RIGHT ROWS ARE PRESENT"
----------------------------------------------------------
A test listing the expected rows would have to be updated alongside the
templates and would then agree with them by construction — the hand-copied
fixture trap (§0.6). These assert the RELATION instead:

    the page number on a contents row identifies a section of this document,
    and that section's own heading is the label on the row.

That cannot pass while any of the three defects is present, and it needs no
expected values, so it keeps holding when the page set changes.

THE TEST THIS REPLACES WAS A SUBSTRING MATCH AND WENT ON FAILING AFTER THE FIX.
`"Market Trends" in html` also matches the CSS comment
`/* ── Overview / Executive Summary Page ── */` in every theme's stylesheet, so
the old strict xfail stayed red for a reason that had nothing to do with the
defect. §0.6's rule, met again in the fix for the defect it was guarding:
match the thing, not text that contains the thing.
"""
import os
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
os.environ.setdefault("DATABASE_URL", "postgresql://fake/fake")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")

from worker.property_builder import (  # noqa: E402
    CONTENTS_OMITS,
    PAGE_ORDER,
    THEME_TEMPLATES,
    PropertyReportBuilder,
    paginate,
)

from test_property_production_render import report_data  # noqa: E402

THEMES = sorted(THEME_TEMPLATES)

#: A rendered page. Themes differ in the trailing classes, never in the first.
SECTION = re.compile(r'<section class="page[ "]')

#: The heading each page carries. Five themes, five class names for one idea
#: — and `aerial-title`, which two themes use and the first version of this
#: regex missed, so `_heading` returned None and the test failed on a page
#: that was correct. A selector is part of the test; a miss reads as a defect.
HEADING = re.compile(
    r'class="(?:page-header-title|property-title|section-title|aerial-title|h)"'
    r'[^>]*>\s*([^<]*?)\s*(?:<|$)', re.S)

#: A contents row, in either markup dialect.
ROW = re.compile(
    r'<(?:div|span) class="(?:contents-num|num)">([^<]*)</(?:div|span)>.*?'
    r'<(?:div|span) class="(?:contents-text|name)">([^<]*)</(?:div|span)>.*?'
    r'<(?:div|span) class="(?:contents-page|pg-num)">([^<]*)</(?:div|span)>',
    re.S)

#: The number a page prints on itself, and ONLY that. `class="num"` is also
#: teal's contents-row ordinal and several themes' statistic tiles, so the
#: match is anchored to the footer that contains it — the difference between
#: reading a page number and reading the digits nearest to one.
FOOTER = re.compile(
    r'class="page-footer"(?:(?!</section>|class="page-footer").)*?'
    r'class="num"[^>]*>\s*(\d\d)\s*<', re.S)


@pytest.fixture(scope="module")
def renders():
    return {t: PropertyReportBuilder(report_data(t)).render_html() for t in THEMES}


@pytest.fixture(scope="module")
def builders():
    return {t: PropertyReportBuilder(report_data(t)) for t in THEMES}


def _sections(html):
    """The document's pages, in order, as raw HTML."""
    starts = [m.start() for m in SECTION.finditer(html)]
    return [html[a:b] for a, b in zip(starts, starts[1:] + [len(html)])]


def _heading(section):
    m = HEADING.search(section)
    return m.group(1).strip() if m else None


def _rows(html):
    """(ordinal, label, page) for each contents row."""
    return [(a.strip(), b.strip(), c.strip()) for a, b, c in ROW.findall(html)]


# ── the relation ───────────────────────────────────────────────────────────

@pytest.mark.parametrize("theme", THEMES)
def test_each_contents_row_points_at_the_page_it_names(theme, renders):
    """The whole of D-121 in one assertion.

    A wrong page number lands on a section headed something else. A drifted
    label disagrees with the heading it lands on. An advertised-but-absent
    page has no section to land on at all.
    """
    html = renders[theme]
    sections = _sections(html)
    rows = _rows(html)
    assert rows, f"{theme} rendered no contents rows at all"

    for ordinal, label, page in rows:
        assert page.isdigit(), (
            f"{theme}: contents row {ordinal!r} ({label!r}) has page {page!r}, "
            f"which is not a number — the page it names did not render"
        )
        n = int(page)
        assert 1 <= n <= len(sections), (
            f"{theme}: contents sends the reader to page {n} of a "
            f"{len(sections)}-page document ({label!r})"
        )
        heading = _heading(sections[n - 1])
        assert heading and heading.upper() == label.upper(), (
            f"{theme}: contents says {label!r} at page {n}; page {n} is headed "
            f"{heading!r}"
        )


@pytest.mark.parametrize("theme", THEMES)
def test_the_number_a_page_prints_is_its_own_position(theme, renders):
    """The other half, and the one that made the numbers decorative.

    Every theme printed `03` on the overview page and `03` again on the
    aerial page. A footer is only useful if it is the sheet index.
    """
    for i, section in enumerate(_sections(renders[theme]), start=1):
        printed = FOOTER.findall(section)
        assert len(printed) <= 1, (
            f"{theme}: page {i} prints {printed} — more than one page number"
        )
        if printed:
            assert int(printed[0]) == i, (
                f"{theme}: page {i} prints {printed[0]}"
            )


@pytest.mark.parametrize("theme", THEMES)
def test_the_contents_lists_every_page_except_the_cover_and_itself(theme, renders, builders):
    """Not only that it lists nothing absent — that it lists nothing LESS.

    The inverse direction, deliberately: a contents page that silently omits
    a page the reader is holding is the same defect with the sign flipped,
    and a test asserting only "nothing extra" passes on an empty contents
    page. §0.6 — a guard asserting A ⇒ B is half a guard.
    """
    _, expected_keys = paginate(builders[theme].page_set)
    rows = _rows(renders[theme])
    assert len(rows) == len(expected_keys), (
        f"{theme}: {len(rows)} contents rows for {len(expected_keys)} listed "
        f"pages {expected_keys}"
    )
    assert [r[0] for r in rows] == [str(i) for i in range(1, len(rows) + 1)] or \
           [r[0] for r in rows] == [f"{i:02d}" for i in range(1, len(rows) + 1)], (
        f"{theme}: contents ordinals are {[r[0] for r in rows]}"
    )


def test_the_cover_and_the_contents_page_are_the_two_that_are_not_listed():
    """`CONTENTS_OMITS` is the claim; this is the check on it."""
    assert set(CONTENTS_OMITS) == {"cover", "contents"}
    numbers, keys = paginate(PAGE_ORDER)
    assert "cover" not in keys and "contents" not in keys
    assert set(keys) | set(CONTENTS_OMITS) == set(PAGE_ORDER)
    assert numbers["cover"] == 1, "the cover is page one; a reader counts it"


def test_page_numbers_follow_the_document_order_not_the_page_set_order():
    """`selected_pages` is membership. The templates fix the sequence.

    A caller passing `["range", "cover", "aerial"]` gets the same document as
    one passing `["cover", "aerial", "range"]`, so enumerating `page_set`
    would number a document that is not the one being rendered.
    """
    shuffled, _ = paginate(["range", "cover", "aerial", "contents"])
    assert shuffled == {"cover": 1, "contents": 2, "aerial": 3, "range": 4}


def test_a_dropped_page_renumbers_everything_after_it():
    """`market_trends` and `overview` are removed when their data does not
    arrive, which is why `paginate` runs after the drops rather than before."""
    full, _ = paginate(PAGE_ORDER)
    without, _ = paginate([p for p in PAGE_ORDER if p != "market_trends"])
    assert full["comparables"] == without["comparables"] + 1
    assert full["aerial"] == without["aerial"], "a page BEFORE the drop moved"


# ── a page set that is not the default ─────────────────────────────────────
#
# THE DEFAULT SET MAKES SEVERAL OF THE OLD LITERALS ACCIDENTALLY CORRECT, and a
# regression written against it can pass for that reason. Restoring bold's
# literal `05` on the analysis page broke nothing — analysis IS page 5 in the
# seven-page default. The literal only shows as a literal once the numbering
# moves, so the same relations are asserted against a set where it has.

#: `property` is the page dropped, not `analysis`. Dropping analysis was the
#: first choice and it proved nothing about that page: a literal on a section
#: that does not render is never emitted, so restoring bold's `05` there still
#: passed. Dropping `property` instead SHIFTS analysis from 5 to 4, comparables
#: from 6 to 5 and range from 7 to 6 — three literals that are correct in the
#: default set and wrong here, which is what a regression needs to see.
SHORT_SET = ["cover", "contents", "aerial", "analysis", "comparables", "range"]


@pytest.fixture(scope="module")
def short_renders():
    out = {}
    for t in THEMES:
        data = dict(report_data(t))
        data["selected_pages"] = list(SHORT_SET)
        out[t] = PropertyReportBuilder(data).render_html()
    return out


@pytest.mark.parametrize("theme", THEMES)
def test_dropping_a_page_renumbers_the_ones_after_it(theme, short_renders):
    """Without `property`, analysis is page 4, comparables 5 and range 6.

    Under the default set they are 5, 6 and 7 — which is what every theme
    used to print. Any surviving literal is wrong here by exactly one.
    """
    for i, section in enumerate(_sections(short_renders[theme]), start=1):
        printed = FOOTER.findall(section)
        if printed:
            assert int(printed[0]) == i, (
                f"{theme}, six-page set: page {i} prints {printed[0]} — a "
                f"literal from the seven-page default, one too high"
            )


@pytest.mark.parametrize("theme", THEMES)
def test_the_contents_of_a_shorter_report_still_points_at_real_pages(theme, short_renders):
    html = short_renders[theme]
    sections = _sections(html)
    rows = _rows(html)
    assert len(rows) == len(SHORT_SET) - len(CONTENTS_OMITS)
    assert "Property Information" not in {label for _, label, _ in rows}, (
        "the contents lists a page this report does not contain"
    )
    for _, label, page in rows:
        heading = _heading(sections[int(page) - 1])
        assert heading and heading.upper() == label.upper(), (
            f"{theme}, six-page set: contents says {label!r} at page {page}; "
            f"that page is headed {heading!r}"
        )
