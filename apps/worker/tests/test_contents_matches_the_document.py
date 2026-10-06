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

from _template_chain import SELF_CONTAINED_THEMES, SHARED_THEMES  # noqa: E402

#: SELF-CONTAINED THEMES ONLY, for everything in this file that reads a
#: contents page.
#:
#: Design's architecture has no contents page — six pages, and a table of
#: contents for six is a page spent telling the reader there are five others.
#: So the numbering property this file is about ("the contents agrees with the
#: document") has no subject on the shared architecture, and the property that
#: REPLACES it is asserted in `test_the_shared_architecture_numbers_its_own
#: _pages` below: the footers run 1..N with no gaps, N is the number of sheets,
#: and no sheet claims to be a contents page.
#:
#: Narrowed rather than skipped: a `pytest.skip` on a theme would leave the
#: file silent about half the themes, and the reason it is silent would live
#: in a skip message nobody reads.
THEMES = SELF_CONTAINED_THEMES
ALL_THEMES = sorted(THEME_TEMPLATES)

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


# ── the page that shifts everything after it ───────────────────────────────
#
# `overview` renders SECOND, before the contents page itself, so its presence
# moves every other page by one INCLUDING the contents page's own number, and
# puts a contents row pointing at a page the reader has already passed. It is
# the page most able to break numbering and, until now, the only one no render
# had ever numbered: it needs an OpenAI key, is dropped silently without one,
# and was covered by `paginate()`'s unit tests alone.
#
# No key is needed. `render_html` reads `report_data["overview_text"]` first
# ("allow pre-injection", property_builder.py:1853) and only calls the model
# when that is absent — so supplying the text is enough to render the page.
# `market_trends_data` is injectable the same way. The nine-page document has
# never been rendered in a test before this one.

FULL_SET = list(PAGE_ORDER)


@pytest.fixture(scope="module")
def full_renders():
    from worker.compute.market_trends import SAMPLE_MARKET_TRENDS
    out = {}
    for t in THEMES:
        data = dict(report_data(t))
        data["selected_pages"] = list(FULL_SET)
        data["overview_text"] = "A short executive summary, injected."
        data["market_trends_data"] = SAMPLE_MARKET_TRENDS
        out[t] = PropertyReportBuilder(data).render_html()
    return out


@pytest.mark.parametrize("theme", THEMES)
def test_every_page_renders_when_the_whole_set_is_asked_for(theme, full_renders):
    """The floor the rest stand on: nine sections, or the numbering below is
    asserting about a document that did not happen."""
    assert len(_sections(full_renders[theme])) == len(FULL_SET), (
        f"{theme}: asked for {len(FULL_SET)} pages, rendered "
        f"{len(_sections(full_renders[theme]))} — a page was dropped and the "
        f"numbering assertions below would pass against the wrong document"
    )


@pytest.mark.parametrize("theme", THEMES)
def test_overview_present_shifts_the_contents_page_itself(theme, full_renders):
    """The case `paginate()`'s unit tests could not reach.

    `overview` is page 2, so the contents page is page 3 rather than 2 and
    every listed page moves by one. A literal anywhere in this chain is wrong
    by exactly that.
    """
    sections = _sections(full_renders[theme])
    printed = {}
    for i, section in enumerate(sections, start=1):
        found = FOOTER.findall(section)
        if found:
            printed[i] = int(found[0])
    assert printed, f"{theme}: the nine-page render printed no page numbers"
    for position, number in printed.items():
        assert number == position, (
            f"{theme}, nine-page set: page {position} prints {number}"
        )


@pytest.mark.parametrize("theme", THEMES)
def test_the_contents_lists_a_page_that_comes_before_it(theme, full_renders):
    """`overview` is listed at page 2 by a contents page that is page 3.

    A row pointing BACKWARDS is legitimate here and is the shape a numbering
    scheme anchored to "the contents page is page 2" gets wrong.
    """
    html = full_renders[theme]
    sections = _sections(html)
    rows = _rows(html)
    assert len(rows) == len(FULL_SET) - len(CONTENTS_OMITS)

    first_ordinal, first_label, first_page = rows[0]
    assert first_label.upper() == "PROPERTY OVERVIEW", (
        f"{theme}: the first contents row is {first_label!r}, not the "
        f"overview page — the nine-page order changed"
    )
    assert int(first_page) == 2, (
        f"{theme}: overview is listed at page {first_page}, and it renders "
        f"second"
    )
    for _, label, page in rows:
        heading = _heading(sections[int(page) - 1])
        assert heading and heading.upper() == label.upper(), (
            f"{theme}, nine-page set: contents says {label!r} at page {page}; "
            f"that page is headed {heading!r}"
        )


@pytest.mark.parametrize("theme", THEMES)
def test_the_same_page_is_numbered_differently_in_the_three_sets(theme, renders, short_renders, full_renders):
    """THE TWO-SETS RULE, STATED AS AN ASSERTION.

    A derived number and a lucky literal are indistinguishable on one page
    set — restoring bold's literal `05` on the analysis page passed against
    the seven-page default because analysis IS page 5 there. So `comparables`
    is checked across all three: page 5 without `property`, 6 in the default,
    8 with everything. No single literal satisfies all three.
    """
    def comparables_page(html):
        rows = {label.upper(): int(page) for _, label, page in _rows(html)}
        return rows["SALES COMPARABLES"]

    seen = {
        "six-page (no property)": comparables_page(short_renders[theme]),
        "seven-page default": comparables_page(renders[theme]),
        "nine-page (everything)": comparables_page(full_renders[theme]),
    }
    assert seen == {
        "six-page (no property)": 5,
        "seven-page default": 6,
        "nine-page (everything)": 8,
    }, f"{theme}: {seen}"
    assert len(set(seen.values())) == 3, (
        f"{theme}: the same page got the same number in every set, so these "
        f"renders cannot tell a derived number from a literal"
    )


# ── the shared architecture's own numbering property ───────────────────────

import pytest  # noqa: E402  (already imported above; harmless and explicit)


@pytest.mark.parametrize("theme", SHARED_THEMES)
def test_the_shared_architecture_numbers_its_own_pages(theme):
    """What replaces "the contents agrees with the document".

    There is no contents page to agree with, so the assertion is on the thing
    a reader actually uses to tell whether a page is missing: the footer.

    Four claims, and the fourth is the one that would have caught D-121:
      1. every sheet carries a "Page n of N" footer
      2. the n values are 1..N with no gaps and no repeats
      3. N equals the number of sheets rendered
      4. no sheet is a contents page

    (3) is the half D-121 was about — a total computed before the conditional
    drops names a document that is not the one being rendered.
    """
    html = PropertyReportBuilder(report_data(theme)).render_html()
    sheets = re.findall(r'<section class="sheet sheet-(\w+)"', html)
    feet = re.findall(r"Page (\d+) of (\d+)", html)

    assert len(feet) == len(sheets), (
        f"{theme}: {len(sheets)} sheets and {len(feet)} page footers"
    )
    numbers = [int(n) for n, _ in feet]
    totals = {int(t) for _, t in feet}
    assert numbers == list(range(1, len(sheets) + 1)), (
        f"{theme}: page numbers are {numbers}, not 1..{len(sheets)}"
    )
    assert totals == {len(sheets)}, (
        f"{theme}: the footers claim {sorted(totals)} pages and "
        f"{len(sheets)} rendered — a total computed before the conditional "
        f"drops names a different document (D-121)"
    )
    assert "contents" not in sheets, (
        f"{theme} rendered a contents page. The shared architecture has none; "
        f"if one came back, this file's other gates apply to it again."
    )
