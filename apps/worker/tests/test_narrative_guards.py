"""A narrative that does not fit is a generation failure, not a layout one (§7.2).

Two ways the generator can hand back copy the PDF cannot take:

  * the API stops at `max_tokens` and returns a sentence with no end;
  * the model ignores "exactly 2-3 sentences" and writes more than the box holds.

Both used to be returned like any other string. The first put a half sentence in
a customer's PDF under the heading "AI Market Insight"; the second pushed page
1's table down, which is the variability §7.2's fixed box removes. Both now drop
the narrative and log it — every layout already renders without one.
"""

import logging
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from worker import ai_market_narrative as ai  # noqa: E402

CITY = "Irvine"
TYPE = "closed"
DATA = {"city": CITY, "lookback_days": 30, "total_closed": 38,
        "median_close_price": 907500, "avg_dom": 12, "list_to_sale_ratio": 0.982}


def respond(content, finish_reason="stop"):
    r = MagicMock()
    r.status_code = 200
    r.json.return_value = {"choices": [{"message": {"content": content},
                                        "finish_reason": finish_reason}]}
    return r


@pytest.fixture
def calling(monkeypatch):
    """Force the real request path: key present, cache absent."""
    monkeypatch.setattr(ai, "OPENAI_API_KEY", "sk-test-not-a-real-key")
    monkeypatch.setattr(ai, "_redis", lambda: None)
    sent = {}

    def install(response):
        import httpx
        monkeypatch.setattr(
            httpx, "post",
            lambda *a, **k: (sent.update(k.get("json") or {}), response)[1])
    return install


def test_a_narrative_the_api_cut_at_max_tokens_is_dropped(calling, caplog):
    cut = "Inventory held near two months of supply and closed sales tracked ahead of the"
    calling(respond(cut, finish_reason="length"))
    with caplog.at_level(logging.ERROR):
        assert ai.generate_market_pdf_narrative(TYPE, CITY, DATA) is None
    assert "max_tokens" in caplog.text
    assert "mid-sentence" in caplog.text


def test_a_narrative_longer_than_the_box_is_dropped(calling, caplog):
    too_long = "The Irvine market held steady this period. " * 20
    assert len(too_long) > ai.NARRATIVE_MAX_CHARS
    calling(respond(too_long))
    with caplog.at_level(logging.ERROR):
        assert ai.generate_market_pdf_narrative(TYPE, CITY, DATA) is None
    assert str(ai.NARRATIVE_MAX_CHARS) in caplog.text


def test_a_narrative_exactly_at_the_budget_is_kept(calling):
    """The boundary, from the inside. Without this, both guards could be off by
    one in the strict direction and every narrative of a normal length would be
    silently discarded — a failure that looks like 'the AI is not configured'."""
    at_budget = "x" * ai.NARRATIVE_MAX_CHARS
    calling(respond(at_budget))
    assert ai.generate_market_pdf_narrative(TYPE, CITY, DATA) == at_budget


def test_an_ordinary_narrative_still_comes_back(calling):
    ordinary = ("The Irvine market showed balanced activity this period, with inventory "
                "holding near two months of supply. Median pricing held firm while days "
                "on market drifted upward.")
    assert len(ordinary) <= ai.NARRATIVE_MAX_CHARS
    calling(respond(ordinary))
    assert ai.generate_market_pdf_narrative(TYPE, CITY, DATA) == ordinary


def test_a_quoted_narrative_is_unwrapped_before_it_is_measured(calling):
    """The existing unwrap strips surrounding quotes. It must run BEFORE the
    budget check, or a quoted narrative is measured two characters too long —
    which at the boundary decides whether a customer gets a narrative."""
    body = "y" * ai.NARRATIVE_MAX_CHARS
    calling(respond(f'"{body}"'))
    assert ai.generate_market_pdf_narrative(TYPE, CITY, DATA) == body
