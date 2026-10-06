"""
D-125 — no number in a property report wears a `.0`.

`_safe_num` returns `float(val)` and the analysis table printed it raw, so
every cell that is not currency-formatted carried one:

    Living Area   786.0    770.0    940.0    912.0
    Year Built    1949.0   1910.0   1953.0   1952.0
    Bedrooms      2.0      3.0      2.0      3.0
    Bathrooms     1.0      1.0      1.0      1.0

`1949.0` as a year and `2.0` as a bedroom count read as machine output in a
document a seller is meant to take seriously.

WHY THE GATE IS ON THE RENDER AND NOT ON THE FILTER
---------------------------------------------------
`format_measure` has its own unit tests below and they are the cheap half.
The defect was never that the formatter was wrong — there was no formatter.
It was that eleven context fields reached five templates unformatted, and
the only way to know that has stopped being true is to render and look.

Found exactly that way twice while fixing it: formatting `extract_comp_stats`
left the SUBJECT's column at `786.0 / 1949.0 / 2.0` beside three clean comp
columns, which is worse than the original — it reads as the subject being a
different kind of number. A unit test on the filter would have been green
through both states.

AND `int()` IS NOT THE FIX, WHICH IS THE WHOLE DIFFICULTY
----------------------------------------------------------
`1.5` and `2.5` are real bathroom counts; `0.58` is a real distance. A gate
that only forbids `.0` is satisfied by truncating every number in the
document, so the half-values are asserted present in the same tests.
"""
import os
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tests"))

os.environ.setdefault("DATABASE_URL", "postgresql://fake/fake")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")

from worker.property_builder import THEME_TEMPLATES, PropertyReportBuilder  # noqa: E402
from worker.template_filters import format_measure  # noqa: E402

from test_property_production_render import COMPS, report_data  # noqa: E402

THEMES = sorted(THEME_TEMPLATES)

from _template_chain import SHARED_THEMES  # noqa: E402

#: A cell's whole text, so `$1,949.00` and a decimal inside prose are not
#: matched. The defect is a lone number in a table cell wearing a `.0`.
TRAILING_ZERO_CELL = re.compile(r">\s*(-?[\d,]+\.0)\s*<")


def half_values():
    """A fixture where every half-value field genuinely has a half.

    Without this the test passes against `| int` applied everywhere, which
    is the obvious wrong fix and the one that loses `1.5` baths.
    """
    comps = []
    for i, (bath, dist) in enumerate(((1.5, 0.58), (2.5, 0.25), (3.5, 1.75), (2.0, 0.5))):
        c = dict(COMPS[i % len(COMPS)])
        c["address"] = f"{100 + i} Halfway Lane"
        c["bathrooms"] = bath
        c["distance_miles"] = dist
        c["sale_price"] = 500_000 + i * 25_000
        c["price"] = c["sale_price"]
        comps.append(c)
    return comps


def rendered(theme, **sitex):
    data = dict(report_data(theme))
    data["comparables"] = half_values()
    data["sitex_data"] = {**data["sitex_data"], **sitex}
    return PropertyReportBuilder(data).render_html()


# ── the render, which is the gate ──────────────────────────────────────────

@pytest.mark.parametrize("theme", THEMES)
def test_no_cell_in_a_property_report_reads_as_a_float(theme):
    html = rendered(theme, bathrooms=1.5, stories=2, bedrooms=3, year_built=1949)
    hits = sorted(set(TRAILING_ZERO_CELL.findall(html)))
    assert not hits, (
        f"{theme} prints {hits}. A year is 1949 and a bedroom count is 2; "
        f"`1949.0` reads as machine output in a document a seller is meant "
        f"to take seriously (D-125)."
    )


@pytest.mark.parametrize("theme", THEMES)
def test_a_genuine_half_survives(theme):
    """The other direction, and the reason `int()` is not the fix.

    `1.5` baths and `0.58` miles are real values. A gate that only forbade
    `.0` would be satisfied by truncating the document.
    """
    html = rendered(theme, bathrooms=1.5)
    assert ">1.5<" in html or "1.5</" in html or ">1.5 " in html or " 1.5<" in html, (
        f"{theme}: 1.5 bathrooms did not survive formatting — the `.0` fix "
        f"truncated a real half"
    )
    assert "0.58" in html, f"{theme}: a 0.58-mile distance was rounded away"


@pytest.mark.parametrize("theme", THEMES)
def test_the_subject_column_is_formatted_like_the_comp_columns(theme):
    """Found by rendering, after a fix that looked complete.

    Formatting `extract_comp_stats` and not `piq` left `786.0 / 1949.0 / 2.0`
    in the first column of a table whose other three were clean. Worse than
    the defect: it reads as the subject being a different kind of number.
    """
    html = rendered(theme, sqft=786, year_built=1949, bedrooms=2, bathrooms=1.0)
    # CELLS, not the document. `"2.0" in html` matched a coordinate inside an
    # inline SVG path in modern's icon set — ninth outing for
    # substring-is-not-a-construct, and a test that would have reported a
    # formatting defect in a house icon.
    cells = set(TRAILING_ZERO_CELL.findall(html))
    assert not cells & {"786.0", "1949.0", "2.0"}, (
        f"{theme}: the subject's column still prints "
        f"{sorted(cells & {'786.0', '1949.0', '2.0'})} while the comp columns "
        f"beside it do not"
    )
    assert ">786<" in html.replace(" ", "") or ">786" in html
    assert "1949" in html


# ── the filter, which is the cheap half ────────────────────────────────────

@pytest.mark.parametrize("value,expected", [
    (1949.0, "1949"), (1949, "1949"), ("1949.0", "1949"),
    (2.0, "2"), (0.0, "0"),
    (1.5, "1.5"), (2.5, "2.5"), (0.58, "0.58"), (0.25, "0.25"),
    (-1.0, "-1"),
    # Passed through unchanged, which D-137 relies on: ABSENT must survive
    # every filter it meets.
    ("-", "-"), ("N/A", "N/A"), ("", ""),
    (None, "-"),
])
def test_format_measure(value, expected):
    assert format_measure(value) == expected


def test_format_measure_does_not_group_thousands():
    """`1,949` is a wrong year, and Year Built is this filter's commonest
    user. Living Area and Lot Size keep `format_number`, which groups."""
    assert format_measure(1949) == "1949"
    assert format_measure(12345.0) == "12345"


# ── per surface, not just per document ─────────────────────────────────────

@pytest.mark.parametrize("theme", SHARED_THEMES)
def test_a_genuine_half_survives_on_every_surface_that_shows_it(theme):
    """`test_a_genuine_half_survives` asserts "1.5 is SOMEWHERE in the document".

    That is the right property and it is not enough. The redesigned document
    shows bathrooms twice — the cover's 30px stat cell and page 2's detail row
    — and reverting the COVER's formatter to the integer one left the document
    still containing "1.5" on page 2, so the gate stayed green while the first
    number a reader sees was wrong. Found by running the regression, not by
    reading the test.

    So each surface is asserted separately. Added 2026-10-06.
    """
    from worker.property_builder import PropertyReportBuilder
    from test_property_production_render import report_data

    data = dict(report_data(theme))
    data["sitex_data"] = {**data["sitex_data"], "bathrooms": 1.5}
    builder = PropertyReportBuilder(data)
    doc = builder._build_v2_context(
        {"property": builder._build_property_context(),
         "agent": builder._build_agent_context(),
         "stats": builder._build_stats_context(),
         "comparables": builder._build_comparables_context(),
         "audience": "agent", "prepared_for": ""},
        list(builder.V2_PAGE_ORDER))

    cover = next((s for s in doc["hero_stats"] if s["label"] == "Bathrooms"), None)
    assert cover is not None, f"{theme}: bathrooms is not one of the cover stats"
    assert cover["value"] == "1.5", (
        f"{theme}: the cover's bathrooms cell reads {cover['value']!r} — the "
        f"half was truncated on the largest number on the page"
    )

    row = next(r for g in doc["detail_groups"] for r in g["rows"]
               if r["label"] == "Bathrooms")
    assert row["value"] == "1.5", (
        f"{theme}: page 2's bathrooms row reads {row['value']!r}"
    )
