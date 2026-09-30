"""
D-119 — the analysis table showed three comps; the chart beside it showed four.

THREE FAILURES IN FOUR LINES OF CODE, AND THEY SHARED ONE CAUSE: three fixed
slots indexed into a list of any length, with nothing checking that the three
came out distinct or that the reader was told how many there were.

    low_comp  = sorted_by_price[0]
    high_comp = sorted_by_price[-1]
    med_idx   = len(sorted_by_price) // 2
    med_comp  = sorted_by_price[med_idx]

  1. It silently dropped comps. For four, that is index 0, 2 and -1 — index 1
     is in no column, while the chart directly above drew all four.
  2. "Medium" was not a median. `len // 2` on four price-sorted comps is the
     THIRD-cheapest: $631,500 against a true median of $610,750.
  3. It collapsed below three comps. At n=2 the indices are 0, 1, 1 — one
     listing in two columns, presented as two. At n=1, all three. At n=0,
     `extract_comp_stats({})` returned a full row of zeros and the table
     printed `0`, `$0`, `0` for a property that does not exist.

WHY THE UNIT TESTS USE BARE DICTS AND THE RENDER TESTS DO NOT
---------------------------------------------------------------
`_analysis_columns` is a pure function over a sorted list, so its tests hand
it `{"p": price}` and assert on identity — which comp came out, not what it
renders as. That is the one place a made-up fixture is the right input,
because the function's contract is about SELECTION and nothing else.

Everything about what reaches the page is asserted on a render through
`PropertyReportBuilder`, because the note, the blank columns and the
filters are all things the builder and the templates do between the
selection and the reader (§0.6: a test that supplies its own input proves
the consumer and says nothing about the producer).
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
    ABSENT,
    THEME_TEMPLATES,
    PropertyReportBuilder,
    _analysis_columns,
)

from test_property_production_render import COMPS, report_data  # noqa: E402

THEMES = sorted(THEME_TEMPLATES)


def _rows(prices):
    return [{"p": p} for p in prices]


# ── the selection ──────────────────────────────────────────────────────────

@pytest.mark.parametrize("n", range(0, 13))
def test_no_listing_appears_in_two_columns(n):
    """THE REGRESSION, at every length rather than the one in the report.

    At n=2 the old indices were 0, 1, 1 and at n=1 they were 0, 0, 0 — the
    same listing presented as two properties, or as three.
    """
    low, med, high = _analysis_columns(_rows(range(n)))[:3]
    filled = [c for c in (low, med, high) if c]
    ids = [id(c) for c in filled]
    assert len(ids) == len(set(ids)), (
        f"n={n}: the same listing fills more than one column — "
        f"low={low} medium={med} high={high}"
    )


@pytest.mark.parametrize("n", range(3, 13))
def test_low_is_the_cheapest_and_high_the_dearest(n):
    rows = _rows(range(n))
    low, med, high = _analysis_columns(rows)[:3]
    assert low is rows[0] and high is rows[-1]
    assert low["p"] < med["p"] < high["p"]


def test_medium_is_the_lower_median_not_the_upper():
    """The exact case on the entry: four comps, a Medium of $631,500 against
    a true median of $610,750. The lower median is $590,000."""
    rows = _rows([470_000, 590_000, 631_500, 635_000])
    _, med, _, _ = _analysis_columns(rows)
    assert med["p"] == 590_000, (
        f"Medium is {med['p']}; `len // 2` would give 631500, the "
        f"third-cheapest of four"
    )


@pytest.mark.parametrize("n,expect", [
    (0, (False, False, False)),
    (1, (False, True, False)),   # the median of one element is that element
    (2, (True, False, True)),    # two sales are a spread, not a median
    (3, (True, True, True)),
])
def test_which_columns_are_filled_below_three_comps(n, expect):
    low, med, high = _analysis_columns(_rows(range(n)))[:3]
    assert tuple(bool(c) for c in (low, med, high)) == expect


@pytest.mark.parametrize("n", range(0, 8))
def test_the_note_says_how_many_comps_it_summarised(n):
    note = _analysis_columns(_rows(range(n)))[3]
    assert note, f"n={n} produced no note"
    if n >= 3:
        assert str(n) in note, f"n={n}: the note does not name the count — {note!r}"


# ── what reaches the page ──────────────────────────────────────────────────

def _render(theme, comps):
    data = dict(report_data(theme))
    data["comparables"] = comps
    return PropertyReportBuilder(data).render_html()


def _price_row(html):
    foot = re.search(r"<tfoot>.*?</tfoot>", html, re.S)
    block = foot.group(0) if foot else html
    return [re.sub("<[^>]+>", "", c).strip()
            for c in re.findall(r"<td[^>]*>(.*?)</td>", block, re.S)]


@pytest.mark.parametrize("theme", THEMES)
def test_the_page_says_how_many_comps_the_table_summarises(theme):
    """A three-column table beside a four-bar chart, with nothing saying
    three of four, reads as the whole set."""
    html = _render(theme, COMPS)
    note = re.search(r'class="analysis-note"[^>]*>\s*([^<]*?)\s*<', html)
    assert note, f"{theme} renders no count note"
    assert str(len(COMPS)) in note.group(1), (
        f"{theme}'s note does not name the {len(COMPS)} comps it summarised: "
        f"{note.group(1)!r}"
    )


@pytest.mark.parametrize("theme", THEMES)
def test_an_empty_column_is_empty_and_not_a_row_of_zeros(theme):
    """Two comps have no median. The Medium column used to print `0`, `$0`
    and a year built of `0` for a property that does not exist — D-137's
    rule, in the one place `extract_comp_stats` could be handed `{}`."""
    html = _render(theme, COMPS[:2])
    cells = _price_row(html)
    assert cells, f"{theme} rendered no price row"
    assert "$0" not in cells, (
        f"{theme}: a column with no listing behind it printed a price — {cells}"
    )
    assert ABSENT in cells, (
        f"{theme}: the medium column of a two-comp report should be {ABSENT!r} "
        f"— {cells}"
    )


@pytest.mark.parametrize("theme", THEMES)
def test_no_comp_reaches_two_columns_of_the_rendered_table(theme):
    """The same assertion as the unit test, through the render, because the
    duplication was visible on the page rather than in the function."""
    html = _render(theme, COMPS[:2])
    prices = [c for c in _price_row(html)[2:] if c not in (ABSENT, "")]
    assert len(prices) == len(set(prices)), (
        f"{theme}: a price appears in two columns — {prices}"
    )


@pytest.mark.parametrize("theme", THEMES)
def test_with_no_comps_at_all_the_table_prints_nothing_rather_than_zeros(theme):
    html = _render(theme, [])
    cells = _price_row(html)
    assert "$0" not in cells, f"{theme}: a zero-comp report priced its columns — {cells}"
    note = re.search(r'class="analysis-note"[^>]*>\s*([^<]*?)\s*<', html)
    assert note and "No comparable sales" in note.group(1), (
        f"{theme}: nothing on the page says the search returned nothing"
    )
