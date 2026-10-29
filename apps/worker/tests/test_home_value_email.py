"""The home-value email (Design's 5th package), and what it must never say.

THE DECISION THIS FILE HOLDS: NO ESTIMATE (owner, 2026-10-28). The number
stays in the report beside the sales it comes from; alone in an email it reads
like an appraisal. Held twice: `home_value_email_html` has no parameter that
could carry one, and the rendered email contains no price.

Contrast in light and dark mode is measured by `test_email_dark_mode.py`.
"""
import ast
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import email_fixtures  # noqa: E402,F401  — pins the render date
from worker.email.home_value import home_value_email_html  # noqa: E402
from worker.email.template import PLATFORM_POSTAL_ADDRESS  # noqa: E402

TASKS = Path(__file__).resolve().parents[1] / "src/worker/tasks.py"


def render(**kw):
    base = dict(report_url="https://www.trendyreports.io/r/abc", address="14 Sandpiper Ln",
                city="Irvine", requester_first_name="Tom", agent_name="Dana Ortiz",
                agent_title="Broker Associate", company_name="Marisol Ridge Realty",
                agent_phone="(626) 555-0134", agent_email="dana@example.test",
                primary_color="#1B365D")
    base.update(kw)
    return home_value_email_html(**base)


# ── no estimate ────────────────────────────────────────────────────────────

def test_the_builder_cannot_be_handed_an_estimate():
    import inspect
    params = inspect.signature(home_value_email_html).parameters
    leaked = [p for p in params if re.search(r"estimate|value|price|range|confidence|^comps?$|comparable", p)]
    assert not leaked, f"home_value_email_html takes {leaked}: the email carries no estimate"


def test_the_email_contains_no_price():
    html = render()
    assert not re.search(r"\$\s?\d", html), "a dollar figure reached the home-value email"
    for word in ("Estimated value", "Likely range", "Confidence"):
        assert word not in html


def test_the_task_passes_nothing_estimate_shaped():
    """The call site in the 300-line Celery task, read as code (AST)."""
    calls = [n for n in ast.walk(ast.parse(TASKS.read_text()))
             if isinstance(n, ast.Call) and getattr(n.func, "id", None) == "home_value_email_html"]
    assert len(calls) == 1
    values = [ast.unparse(k.value) for k in calls[0].keywords]
    assert not [v for v in values if "estimate" in v or "comparables" in v], values


# ── what it says ───────────────────────────────────────────────────────────

@pytest.mark.parametrize("claim", [
    "PDF", "pages", "MB", "¾ mile", "90 days", "what we corrected",
    "nothing else will come", "no pitch", "Powered by",
])
def test_no_claim_from_the_mock_that_is_not_true_here(claim):
    assert claim not in render()


def test_the_requester_is_greeted_by_name_or_not_at_all():
    assert "Tom, your report is ready." in render()
    assert ">Your report is ready.<" in render(requester_first_name=None)


def test_our_address_beside_our_name_and_never_the_mocks():
    html = render()
    assert f"Sent by TrendyReports · {PLATFORM_POSTAL_ADDRESS} · on behalf of Dana Ortiz" in html
    assert "Marisol Ridge Realty · 440" not in html
    for wrong in ("Jamboree", "92612", "MacArthur"):
        assert wrong not in html


def test_the_accounts_own_address_when_it_has_one():
    html = render(postal_address="9 Affiliate Way, Irvine, CA 92602")
    assert "Marisol Ridge Realty · 9 Affiliate Way, Irvine, CA 92602" in html
    assert PLATFORM_POSTAL_ADDRESS not in html


# ── escaping and links ─────────────────────────────────────────────────────

@pytest.mark.parametrize("field", ["requester_first_name", "company_name", "agent_name", "address"])
def test_every_typed_value_is_escaped(field):
    html = render(**{field: '<img src=x onerror="alert(1)">'})
    assert "<img src=x" not in html and "&lt;img src=x" in html


def test_a_javascript_report_url_is_not_linked():
    assert "javascript:" not in render(report_url="javascript:alert(1)")


def test_call_and_text_link_a_dialable_number_and_only_that():
    html = render()
    assert 'href="tel:+16265550134"' in html and 'href="sms:+16265550134"' in html
    bare = render(agent_phone="call me after 5")
    assert "tel:" not in bare and "sms:" not in bare
    assert "call me after 5" in bare, "an undialable number is still shown"


def test_the_email_button_shows_the_address_not_the_word():
    assert ">dana@example.test</a>" in render()


# ── the agent the details belong to ────────────────────────────────────────

def test_the_brand_lookup_is_the_reports_own_agent():
    """
    D-306. The query that fills the PDF and this email's agent block read
    `LIMIT 1` over every user on the account. Scoped to `agent_id`, the report's
    own agent, or another user's photo, email and licence can ship.
    """
    src = TASKS.read_text()
    i = src.index("COALESCE(u.photo_url, u.avatar_url)", src.index("GENERATE BRANDED PDF REPORT"))
    query = src[i:src.index('"""', i)]
    call = src[src.index('"""', i):src.index("brand_row = cur.fetchone()", i)]
    assert "u.id = %s::uuid" in query and "LIMIT 1" not in query
    assert "agent_id" in call
