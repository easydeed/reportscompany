"""
D-115 / B6 — the bar and the number beside it were pictures of different things.

`_band_rows` drew each bar as `count / max_count` — the band's share of the
LARGEST band — while the label printed its share of the TOTAL. Both correct in
isolation. The pairing was the defect: the register's example is Move-Up at
**43% beside a bar filled to 100%**, because Move-Up *was* the largest band.

A reader takes a bar as a picture of the number printed next to it. It was a
picture of a different number, and the more dominant a band the wider the lie.

WHY THESE TESTS ASSERT A RELATION AND NOT WIDTHS
--------------------------------------------------
Every assertion below is *the bar equals the label on this row*, read out of
the rendered HTML. Nothing lists expected widths: a table of them would have
to be updated alongside the code and would then agree with it by construction
— the hand-copied fixture trap (§0.6). The relation cannot hold while the
defect is present and needs no maintenance when the fixture changes.

THE ONE CASE THAT MUST NOT PASS BY COINCIDENCE
------------------------------------------------
In a two-band split of 50/50 the old code and the new agree on every row, and
in `100/0` they agree too. The regression cases here are deliberately
lopsided, because a dominant band is where `count/max_count` and `count/total`
diverge most — and that is the case the register actually reported.
"""
import os
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
os.environ.setdefault("AI_INSIGHTS_ENABLED", "false")
os.environ.setdefault("DATABASE_URL", "postgresql://fake/fake")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")

from worker.email.template import (  # noqa: E402
    _band_rows,
    _label_share,
    schedule_email_html,
)

from email_fixtures import BASE_BRAND, LISTINGS, METRICS  # noqa: E402

#: Lopsided on purpose — see the module docstring. Move-Up is 64 of 100, so
#: `count/max_count` says 100% and `count/total` says 64%.
BANDS = [
    {"name": "Starter", "range": "under $700K", "count": 12},
    {"name": "Move-Up", "range": "$700K–$1.1M", "count": 64},
    {"name": "Luxury", "range": "$1.1M+", "count": 24},
]


def render(bands):
    return schedule_email_html(
        account_name="Marisol Ridge Realty", report_type="price_bands",
        city="La Verne", zip_codes=None, lookback_days=30,
        metrics={**METRICS, "bands": bands},
        pdf_url="https://assets.example.test/r/1.pdf",
        unsubscribe_url="https://app.example.test/unsub?token=" + "a" * 64,
        brand=dict(BASE_BRAND), listings=LISTINGS, sender_type="REGULAR",
        total_found=50, total_shown=8,
    )


#: One band's row: the filled cell's width, then the label's percentage. The
#: filled cell is the one with a background that is not the track's #e5e7eb.
ROW = re.compile(
    r'<td width="(\d+)%" style="height: 24px; background-color: (?!#e5e7eb)'
    r'[^"]*"></td>.*?<span style="[^"]*">\s*(\d+)%\s*</span>', re.S)


def rendered_pairs(html):
    """(bar width, printed percentage) for every band row that drew a bar."""
    return [(int(w), int(p)) for w, p in ROW.findall(html)]


# ── the relation ───────────────────────────────────────────────────────────

def test_every_bar_is_the_width_of_the_number_printed_beside_it():
    pairs = rendered_pairs(render(BANDS))
    assert pairs, "no band rows rendered; the assertion below would be vacuous"
    mismatched = [(w, p) for w, p in pairs if w != p]
    assert not mismatched, (
        f"bar width does not match the printed share: {mismatched} "
        f"(all rows: {pairs})"
    )


def test_the_dominant_band_does_not_fill_the_track():
    """THE REGISTER'S CASE. Move-Up is 64 of 100 listings — the largest band,
    so the old code drew it at 100% beside a label reading 64%."""
    pairs = rendered_pairs(render(BANDS))
    widest = max(w for w, _ in pairs)
    assert widest == 64, (
        f"the widest bar is {widest}%; Move-Up is 64% of the market and the "
        f"old normalisation would make it 100%"
    )


@pytest.mark.parametrize("counts,expect", [
    ([1, 99], [1, 99]),
    ([50, 50], [50, 50]),
    ([97, 1, 1, 1], [97, 1, 1, 1]),
])
def test_the_relation_holds_across_shapes(counts, expect):
    bands = [{"name": f"B{i}", "range": "-", "count": c}
             for i, c in enumerate(counts)]
    pairs = rendered_pairs(render(bands))
    assert [w for w, _ in pairs] == expect
    assert all(w == p for w, p in pairs)


def test_a_band_whose_share_rounds_to_zero_draws_no_bar_and_keeps_its_count():
    """The 2% floor is gone, and this is what replaces it.

    A floor would draw 2% beside a label reading 0% — this defect again,
    smaller. The listing count is on the row regardless, so the band is not
    invisible; only its bar is, which is what a 0% label says.
    """
    bands = [{"name": "Vast", "range": "-", "count": 999},
             {"name": "One", "range": "-", "count": 1}]
    html = render(bands)
    pairs = rendered_pairs(html)
    assert [w for w, _ in pairs] == [100], (
        f"the 0% band drew a bar: {pairs}"
    )
    assert "1 listings" in html, "the single-listing band vanished from the row"


# ── the helper, where the shapes are cheap to enumerate ────────────────────

@pytest.mark.parametrize("label,expect", [
    ("43%", 43), ("0%", 0), ("100%", 100), ("7 %", 7), ("2.6%", 3),
    ("", None), ("x", None), (None, None), ("-", None),
])
def test_the_share_is_read_from_the_label_the_reader_sees(label, expect):
    assert _label_share(label) == expect


def test_an_unreadable_label_draws_no_bar_rather_than_a_guess():
    rows = _band_rows([("Odd", "5", "n/a", False)], "#1B365D", "#B8860B")
    assert rows[0]["bar_pct"] == 0
    assert rows[0]["empty_pct"] == 100


def test_the_bar_is_parsed_from_the_label_not_recomputed():
    """Deriving both from `count / total` would let them differ by a rounding
    step — the same defect one order of magnitude down. The width comes from
    the string that is printed, so it cannot.
    """
    # A label that disagrees with its own count: the bar follows the LABEL,
    # because the label is what the reader is comparing the bar against.
    rows = _band_rows([("Odd", "999", "12%", False)], "#1B365D", "#B8860B")
    assert rows[0]["bar_pct"] == 12
