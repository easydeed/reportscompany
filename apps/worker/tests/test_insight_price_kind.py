"""
D-085 — a sentence must name the price it means.

THE DEFECT
----------
Three functions resolved one variable by precedence:

    median_price = metrics.get("median_close_price") or metrics.get("median_list_price")

and spent it on sentences that want different things — "homes SOLD at a median
of", "median ASKING price of", "at a median SALE price".

Every one of them rendered correctly, and none was guaranteed to. The precedence
happened to match because of which metrics each builder emits: `market_snapshot`
emits both, so close wins and its sale sentences are right; `new_listings` emits
only a list price, so its asking sentence is right. Correct by coincidence,
across two files, with nothing stating the dependency.

THE DIRECTION OF THE FAILURE IS WHAT MAKES IT WORTH A TEST
----------------------------------------------------------
`build_inventory_result` now has closed listings and could compute a close
price. Adding one is an obviously correct change to a builder, reviewed on its
own terms, in a different file — and it would have turned

    "42 active listings at a median of $450,000"

into a figure describing homes that had already sold. Nothing would have raised.
The email would just have started saying something else.

Demonstrated before the fix, with a metrics dict carrying only a list price:

    "18 homes sold at a median of $825K"   <- the ASKING price, called a sale

THE ENTRY UNDERCOUNTED IT. D-085 records `_get_insight_paragraph`. The same
precedence is in `_get_quick_take` and `_get_conversation_starter` — three
functions, nine sentences.
"""
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
os.environ.setdefault("AI_INSIGHTS_ENABLED", "false")
os.environ.setdefault("DATABASE_URL", "postgresql://fake/fake")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")

from worker.email.template import (  # noqa: E402
    ASKING, EITHER, SOLD, _get_conversation_starter, _get_insight_paragraph,
    _get_quick_take, _median,
)

CLOSE = 812000
LIST = 825000
CLOSE_STR = "$812K"
LIST_STR = "$825K"

BASE = {"total_active": 42, "total_closed": 18, "months_of_inventory": 2.3, "avg_dom": 24}
BOTH = dict(BASE, median_close_price=CLOSE, median_list_price=LIST)
LIST_ONLY = dict(BASE, median_list_price=LIST)
CLOSE_ONLY = dict(BASE, median_close_price=CLOSE)
NEITHER = dict(BASE)

ALL_TYPES = ["market_snapshot", "new_listings", "inventory", "closed",
             "price_bands", "open_houses", "new_listings_gallery", "featured_listings"]


def insight(rt, metrics):
    return _get_insight_paragraph(rt, "La Verne", metrics, 30)


# ---------------------------------------------------------------------------
# The resolver
# ---------------------------------------------------------------------------

def test_the_resolver_returns_the_kind_it_was_asked_for():
    assert _median(SOLD, BOTH) == CLOSE_STR
    assert _median(ASKING, BOTH) == LIST_STR
    assert _median(EITHER, BOTH) == CLOSE_STR


def test_a_missing_kind_returns_none_rather_than_the_other_kind():
    """
    THE WHOLE POINT. Returning a fallback here would put the precedence back
    inside the function written to remove it.
    """
    assert _median(SOLD, LIST_ONLY) is None
    assert _median(ASKING, CLOSE_ONLY) is None
    assert _median(SOLD, NEITHER) is None
    # EITHER is the one kind that may substitute, because it claims nothing
    assert _median(EITHER, LIST_ONLY) == LIST_STR


def test_an_unknown_kind_raises():
    """A typo'd kind must not silently become a price."""
    with pytest.raises(ValueError):
        _median("close", BOTH)


# ---------------------------------------------------------------------------
# THE REGRESSION, in the exact shape D-085 predicted
# ---------------------------------------------------------------------------

def test_a_list_price_is_never_reported_as_a_sale():
    """
    The scenario on the entry: a builder starts emitting only one of the two.
    No sentence anywhere may describe a list price as something that sold.
    """
    for rt in ALL_TYPES:
        text = insight(rt, LIST_ONLY)
        if LIST_STR in text:
            assert "sold at a median" not in text, f"{rt}: {text[:160]}"
            assert "median sale price" not in text, f"{rt}: {text[:160]}"
            assert "closed" not in text.split(LIST_STR)[0][-60:], f"{rt}: {text[:160]}"


def test_a_close_price_is_never_reported_as_an_asking_price():
    for rt in ALL_TYPES:
        text = insight(rt, CLOSE_ONLY)
        if CLOSE_STR in text:
            assert "asking price of" not in text, f"{rt}: {text[:160]}"


def test_the_sale_sentences_use_the_close_price():
    assert CLOSE_STR in insight("market_snapshot", BOTH)
    assert LIST_STR not in insight("market_snapshot", BOTH)
    assert CLOSE_STR in insight("closed", BOTH)
    assert LIST_STR not in insight("closed", BOTH)


def test_the_asking_sentences_use_the_list_price():
    assert LIST_STR in insight("new_listings", BOTH)
    assert CLOSE_STR not in insight("new_listings", BOTH)
    assert LIST_STR in insight("inventory", BOTH), "active listings are asks, not sales"
    assert CLOSE_STR not in insight("inventory", BOTH)


# ---------------------------------------------------------------------------
# Degrading, not substituting
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("rt", ALL_TYPES)
@pytest.mark.parametrize("metrics", [BOTH, LIST_ONLY, CLOSE_ONLY, NEITHER],
                         ids=["both", "list_only", "close_only", "neither"])
def test_every_sentence_is_still_well_formed(rt, metrics):
    """
    Dropping a clause must not leave a seam. The first version of this fix
    produced "just hit the market . Current inventory" and "in the last 30 days
    . showing confidence" — the clause went, the spacing did not.
    """
    for fn in (insight(rt, metrics), _get_quick_take(rt, "La Verne", metrics),
               _get_conversation_starter(rt, "La Verne", metrics)):
        assert "  " not in fn, repr(fn)
        assert " ." not in fn, repr(fn)
        assert " ," not in fn, repr(fn)
        assert fn.strip(), "a sentence collapsed to nothing"


@pytest.mark.parametrize("rt", ALL_TYPES)
def test_no_sentence_invents_a_price_when_there_is_none(rt):
    for fn in (insight(rt, NEITHER), _get_quick_take(rt, "La Verne", NEITHER),
               _get_conversation_starter(rt, "La Verne", NEITHER)):
        assert "$" not in fn, f"{rt}: quoted a price from an empty metrics dict: {fn[:120]}"


def test_quick_take_drops_the_claim_rather_than_the_number():
    """
    With no close price, "18 closed transactions at $X median price point" must
    not become "at None" or borrow the asking price — it must become a different
    sentence.
    """
    with_close = _get_quick_take("closed", "La Verne", BOTH)
    without = _get_quick_take("closed", "La Verne", LIST_ONLY)
    assert CLOSE_STR in with_close and "median sale price" in with_close
    assert LIST_STR not in without
    assert "None" not in without
    assert without != with_close and without.strip()
