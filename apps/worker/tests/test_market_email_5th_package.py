"""The rules Design's 5th-package market email rests on, each pinned once.

The layout itself is held by the golden facts (`test_email_render_diff.py`) and
the block declarations (`test_block_structure.py`); the light and dark contrast
by `test_email_contrast.py` and `test_email_dark_mode.py`. What is here are the
claims the email makes in words, which none of those can check:

  * "All of them are in the report" only where the PDF really has them all.
  * Our postal address, never the one in Design's mocks.
  * No "PDF · one page", no "Powered by", no web font.
  * The unsubscribe link carries the class dark mode needs to reach it.
"""
import random
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from email_fixtures import FIXED_DATE, REPORT_TYPES, render  # noqa: E402
from worker.email import template as tmpl  # noqa: E402
from worker.market_builder import PDF_CONFIG  # noqa: E402
from worker.themes import contrast  # noqa: E402

#: Every address that appears in Design's package. All wrong for us; the one in
#: the transactional and home-value mocks is the review's headline finding.
MOCK_ADDRESSES = ("Jamboree", "92612", "MacArthur", "92660")


# ── the truncation note ────────────────────────────────────────────────────

@pytest.mark.parametrize("kind", sorted(PDF_CONFIG))
def test_all_in_the_report_is_said_only_where_the_pdf_has_them_all(kind):
    """
    Design's note reads "Showing 4 of 118. All of them are in the report." For
    the snapshot kinds the PDF is itself a sample (market_snapshot 9,
    price_bands 8, featured_listings 12), so past the cap the second sentence
    is false. Checked against PDF_CONFIG, the PDF's own cap, for a total on
    each side of it.
    """
    cap = PDF_CONFIG[kind]["cap"]
    assert tmpl._pdf_has_all(kind, cap) is True
    assert tmpl._pdf_has_all(kind, cap + 1) is False


def test_the_snapshot_kinds_do_not_promise_the_rest():
    html = render("market_snapshot", "#0D9488")      # 50 available, PDF shows 9
    assert "Showing 8 of 50." in html
    assert "All of them are in the report" not in html


def test_the_catalog_kinds_do():
    html = render("closed", "#0D9488")               # 50 available, PDF shows 200
    assert "Showing 8 of 50. All of them are in the report." in html


@pytest.mark.parametrize("kind", REPORT_TYPES)
def test_the_note_counts_what_the_email_drew(kind):
    """
    The old 2×2 gallery drew 4 listings under a note reading "Showing 8". The
    note now counts the listings rendered, and every layout renders all of them.
    """
    html = render(kind, "#0D9488")
    drawn = len(set(re.findall(r">(\d) Oak St", html)))
    m = re.search(r"Showing (\d+) of", html)
    assert m and int(m.group(1)) == drawn, (kind, drawn, m and m.group(0))


# ── what the footer and the CTA say ────────────────────────────────────────

@pytest.mark.parametrize("kind", REPORT_TYPES)
def test_no_address_from_the_mocks_and_ours_is_present(kind):
    html = render(kind, "#0D9488")
    for wrong in MOCK_ADDRESSES:
        assert wrong not in html, f"{kind}: {wrong!r} from Design's mock reached the email"
    assert tmpl.PLATFORM_POSTAL_ADDRESS in html


@pytest.mark.parametrize("kind", REPORT_TYPES)
def test_no_claim_the_email_cannot_know(kind):
    """
    "PDF · one page": Closed and Inventory run to several. "CRMLS": which MLS
    feeds an account is not known at render time. "a dash means": the email
    prints "N/A", not a dash.
    """
    html = render(kind, "#0D9488")
    for claim in ("one page", "CRMLS", "a dash means", "Powered by"):
        assert claim not in html, f"{kind}: {claim!r}"


def test_the_date_is_the_render_date():
    html = render("market_snapshot", "#0D9488")
    assert html.count(FIXED_DATE.strftime("%B %-d, %Y")) == 2   # masthead + data line


def test_the_unsubscribe_link_reaches_the_dark_palette():
    """
    The link sets its colour inline, so only a class lets the dark rule reach
    it. Without `tr-muted` it measured 3.08:1 on the dark card.
    """
    html = render("market_snapshot", "#0D9488")
    link = re.search(r'<a href="https://app\.example\.test/unsub[^"]*"[^>]*>', html).group(0)
    assert 'class="tr-muted"' in link


# ── the shell ──────────────────────────────────────────────────────────────

def test_the_shell_declares_both_schemes_and_loads_no_font():
    html = render("market_snapshot", "#0D9488")
    assert '<meta name="color-scheme" content="light dark">' in html
    assert "prefers-color-scheme: dark" in html
    assert "fonts.googleapis" not in html and "Outfit" not in html


@pytest.mark.parametrize("brand", ["#1B365D", "#0D9488", "#F59E0B", "#84CC16"])
def test_the_dark_brand_rule_is_this_brands(brand):
    html = render("market_snapshot", brand)
    rule = re.search(r"\.tr-brand\{color:(#[0-9a-f]{6}) !important;\}", html)
    assert rule and rule.group(1) == tmpl._dark_ink(brand)


# ── the tokens ─────────────────────────────────────────────────────────────

def _colours(n=300, seed=7):
    rnd = random.Random(seed)
    return ["#%06x" % rnd.randrange(0x1000000) for _ in range(n)] + [
        "#000000", "#ffffff", "#1B365D", "#F59E0B", "#84CC16", "#FFFF00"]


def test_the_dark_ink_clears_aa_on_the_dark_tint_and_card_for_any_brand():
    for c in _colours():
        ink = tmpl._dark_ink(c)
        assert contrast(ink, tmpl.DARK_TINT) >= 4.5, (c, ink)
        assert contrast(ink, "#1F2937") >= 4.5, (c, ink)


def test_the_light_ink_clears_aa_on_white_and_the_tint_for_any_brand():
    for c in _colours():
        tk = tmpl._tokens(c)
        assert contrast(tk["ink"], "#ffffff") >= 4.5, c
        assert contrast(tk["ink"], tk["tint"]) >= 4.5, c


# ── the headline split ─────────────────────────────────────────────────────

@pytest.mark.parametrize("text,headline,body", [
    ("One sentence.", "One sentence.", ""),
    ("Prices rose. Inventory fell.", "Prices rose.", "Inventory fell."),
    ("The median hit $1.42M this month. Up 2.1%.", "The median hit $1.42M this month.", "Up 2.1%."),
    ("Is it a seller's market? Yes.", "Is it a seller's market?", "Yes."),
    ("No terminal punctuation", "No terminal punctuation", ""),
])
def test_the_insight_splits_at_the_first_sentence(text, headline, body):
    assert tmpl._split_insight(text) == (headline, body)


def test_initials_take_letters_only():
    assert tmpl._initials("Dana Ortiz") == "DO"
    assert tmpl._initials("Marisol Ridge Realty") == "MR"
    assert tmpl._initials("&lt;script&gt; x") == "X"
    assert tmpl._initials("") == ""
