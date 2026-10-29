"""The account emails say what the code does (owner, 2026-10-29).

The copy is ours, built from Design's twelve transactional bodies: their
sentence wherever the code agrees with it, a corrected one where it does not.
Each correction from the review of Design's copy is a test here, so a later
edit that brings the wrong claim back fails:

  * seats are REP seats; an agent gets an account, never a seat;
  * nothing is "paid by" the title company;
  * plan numbers come from `plans`, never typed; none at all if unreadable;
  * no retry, and nothing un-pauses a schedule on upgrade;
  * the limit email's "N more" is the gate's own grace;
  * a rep's pronouns are not known: "they";
  * link lifetimes are the constants the token routes use; an admin reset
    lasts ADMIN_RESET_LINK_TTL, and its link works (D-312);
  * our address, never Design's mock address.
"""
import ast
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "apps/worker/src"))
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")

from api.services import email as em  # noqa: E402
from api.services.usage import evaluate_product_limit, grace_ceiling  # noqa: E402

LIMITS = {"sponsored_free": {"market_reports": 7, "schedules": 2},
          "free": {"market_reports": 4, "schedules": 1}}


def _sent(fn, *args, limits=LIMITS, **kw):
    out = {}
    with patch.object(em.email_service, "send_email_sync", lambda **p: out.update(p) or {"ok": True}), \
         patch.object(em, "_plan_limits", lambda slug: limits.get(slug) if limits else None, create=True):
        getattr(em, fn)(*args, **kw)
    return out


def _all_text(msg):
    return msg["subject"] + "\n" + msg["html"] + "\n" + msg.get("text", "")


AGENT_FACING = [
    ("send_role_invite_email", ("a@x.test", "Ben Carter", "Pacific Coast Title", "tok"), {"role": "sponsored_agent"}),
    ("send_sponsored_agent_welcome_email", ("a@x.test", "Dana", "Pacific Coast Title"), {"rep_name": "Ben Carter"}),
    ("send_rep_welcome_email", ("a@x.test", "Ben", "Pacific Coast Title"), {}),
    ("send_affiliate_welcome_email", ("a@x.test", "Ben"), {}),
]
EVERY = AGENT_FACING + [
    ("send_role_invite_email", ("a@x.test", "Maria Lopez", "Pacific Coast Title", "tok"), {"role": "company_admin"}),
    ("send_role_invite_email", ("a@x.test", "Maria Lopez", "Pacific Coast Title", "tok"), {"role": "title_rep"}),
    ("send_role_invite_email", ("a@x.test", "Maria Lopez", "Acme", "tok"), {"role": "affiliate_admin"}),
    ("send_verification_email", ("a@x.test", "Dana Ortiz", "tok"), {}),
    ("send_password_reset_email", ("a@x.test", "Dana", "tok"), {}),
    ("send_password_reset_email", ("a@x.test", "Dana", "tok"), {"by_admin": True}),
    ("send_limit_warning_email", ("a@x.test", "Dana", 20, 25), {"plan_name": "Growth"}),
    ("send_limit_reached_email", ("a@x.test", "Dana", 25), {"count": 25, "plan_name": "Growth"}),
    ("send_regular_agent_welcome_email", ("a@x.test", "Dana"), {}),
    ("send_company_admin_welcome_email", ("a@x.test", "Maria", "Pacific Coast Title"), {}),
    ("send_rep_change_notice_email", ("a@x.test",), dict(first_name="Dana", company_name="Pacific Coast Title",
                                                          new_rep_name="Ben Carter", new_rep_email="ben@x.test")),
]


def _id(case):
    return case[0] + ("-" + "-".join(f"{k}={v}" for k, v in case[2].items() if k in ("role", "by_admin")))


# ── the corrections ──────────────────────────────────────────────────────────

@pytest.mark.parametrize("case", AGENT_FACING, ids=_id)
def test_an_agent_is_never_given_a_seat_or_told_who_pays(case):
    text = _all_text(_sent(case[0], *case[1], **case[2])).lower()
    assert "seat" not in text, "seats are rep seats; an agent takes none"
    assert "paid" not in text and "pays for" not in text, "nothing is paid by the title company"


@pytest.mark.parametrize("case", EVERY, ids=_id)
def test_no_claim_from_designs_mocks_that_the_code_contradicts(case):
    text = _all_text(_sent(case[0], *case[1], **case[2]))
    lowered = text.lower()
    for wrong in ("try again", "retry", "within the hour", "18575", "jamboree", "92612",
                  "never what", "white-label", "30 seconds", "home-value page", "10 market reports",
                  "10 reports a month",
                  # main's own wording before this change: agents' reports never
                  # carry the company brand (no co-brand), and nobody is on a trial
                  "cascade", "carry your branding", "carrying", "trial account", "8 report types"):
        assert wrong not in lowered, f"{_id(case)} says {wrong!r}"
    assert not re.search(r"\b(he|she|his|her)\b", lowered), f"{_id(case)} assumes a pronoun"
    assert em.PLATFORM_POSTAL_ADDRESS in text


def test_the_rep_is_they_and_what_they_can_see_is_what_the_api_returns():
    """A rep's views return each agent report's pdf_url today, so the welcome
    says they can see the reports — not Design's "never what's in them"."""
    text = _all_text(_sent("send_sponsored_agent_welcome_email", "a@x.test", "Dana", "Pacific Coast Title",
                           rep_name="Ben Carter"))
    assert "Ben Carter is your rep: they can see the reports you make and your schedules." in text
    affiliates = (ROOT / "apps/api/src/api/routes/affiliates.py").read_text()
    assert '"pdf_url": r[5]' in affiliates, (
        "the rep views stopped returning report links: update the welcome to Design's "
        "'they see that reports went out, never what's in them'")


# ── plan numbers come from the table ─────────────────────────────────────────

@pytest.mark.parametrize("case", AGENT_FACING[:4], ids=_id)
def test_the_sponsored_plan_numbers_are_the_tables(case):
    text = _all_text(_sent(case[0], *case[1], **case[2]))
    assert "7 market reports a month" in text and "2 schedules that send" in text


@pytest.mark.parametrize("case", AGENT_FACING[:4] + [EVERY[-3]], ids=_id)
def test_no_number_rather_than_a_guess_when_the_table_cannot_be_read(case):
    text = _all_text(_sent(case[0], *case[1], limits=None, **case[2]))
    assert not re.search(r"\d+ market reports? a month", text)
    assert not re.search(r"\d+ schedules? that send", text)


def test_no_plan_number_is_typed_anywhere_in_the_module():
    text = (ROOT / "apps/api/src/api/services/email.py").read_text()
    assert not re.findall(r"\b\d+\s+(?:market\s+)?(?:reports?|schedules?)\s+(?:per|a)\s+month", text)


# ── the limit emails ─────────────────────────────────────────────────────────

def test_the_grace_ceiling_is_the_gates_own_rule():
    for limit in range(1, 201):
        for used in range(0, 260):
            gate = evaluate_product_limit(used, limit, strict=False)["can_proceed"]
            assert gate == (used < grace_ceiling(limit)), (limit, used)


@pytest.mark.parametrize("limit,count,more", [(25, 25, 3), (3, 3, 1), (10, 10, 1), (25, 28, 0)])
def test_the_limit_email_says_how_many_more_the_gate_allows(limit, count, more):
    text = _all_text(_sent("send_limit_reached_email", "a@x.test", "Dana", limit, count=count))
    if more:
        assert f"You can make {more} more while you decide." in text
    else:
        assert "more while you decide" not in text
    assert "skipped, not sent later" in text
    assert "aren&rsquo;t re-sent" in text or "aren’t re-sent" in text


def test_the_reset_date_is_the_first_of_next_month():
    assert em._next_reset(datetime(2026, 10, 29, tzinfo=timezone.utc)).isoformat() == "2026-11-01"
    assert em._next_reset(datetime(2026, 12, 31, 23, 59, tzinfo=timezone.utc)).isoformat() == "2027-01-01"


def test_the_warning_says_scheduled_reports_do_not_count():
    """`get_usage_counts` excludes reports made by schedules."""
    text = _all_text(_sent("send_limit_warning_email", "a@x.test", "Dana", 20, 25))
    assert "Reports your schedules make don" in text
    usage = (ROOT / "apps/api/src/api/services/usage.py").read_text()
    assert "SELECT 1 FROM schedule_runs sr WHERE sr.report_run_id = rg.id" in usage


# ── link lifetimes are the routes' ───────────────────────────────────────────

def test_each_email_states_the_lifetime_its_token_gets():
    assert "Expires in 24 hours" in _all_text(_sent("send_verification_email", "a@x.test", "D", "t"))
    assert "Expires in 1 hour." in _all_text(_sent("send_password_reset_email", "a@x.test", "D", "t"))
    assert "Expires in 24 hours" in _all_text(_sent("send_password_reset_email", "a@x.test", "D", "t", by_admin=True))
    assert "works for 7 days" in _all_text(_sent("send_role_invite_email", "a@x.test", "B", "C", "t"))


def test_the_routes_mint_tokens_with_the_same_constants():
    """No literal lifetime where a token is created: the email and the
    database read one value."""
    auth = (ROOT / "apps/api/src/api/routes/auth.py").read_text()
    admin = (ROOT / "apps/api/src/api/routes/admin.py").read_text()
    invites = (ROOT / "apps/api/src/api/services/invite_service.py").read_text()
    assert auth.count("+ VERIFY_LINK_TTL") == 2 and "+ RESET_LINK_TTL" in auth
    assert "ADMIN_RESET_LINK_TTL))" in admin
    assert invites.count("INVITE_LINK_TTL),") == 2
    for src in (invites,):
        assert "INTERVAL '7 days'" not in src


def test_an_admin_sent_reset_links_to_the_token(monkeypatch):
    """D-312: the admin route passed (email, token, first_name) to
    (email, user_name, reset_token). Called as the route calls it."""
    from api.routes import admin
    calls = []

    class Tasks:
        def add_task(self, fn, *a, **k):
            calls.append((fn, a, k))

    tree = ast.parse((ROOT / "apps/api/src/api/routes/admin.py").read_text())
    call = next(n for n in ast.walk(tree) if isinstance(n, ast.Call)
                and getattr(n.func, "attr", "") == "add_task"
                and n.args and getattr(n.args[0], "id", "") == "send_password_reset_email")
    env = {"send_password_reset_email": em.send_password_reset_email, "email": "a@x.test",
           "first_name": "Dana", "token": "TOKEN-123", "background_tasks": Tasks()}
    eval(compile(ast.Expression(call), "admin.py", "eval"), env)
    fn, a, k = calls[0]
    msg = {}
    with patch.object(em.email_service, "send_email_sync", lambda **p: msg.update(p) or {"ok": True}):
        fn(*a, **k)
    assert "reset-password?token=TOKEN-123" in msg["html"], "the admin reset link does not carry the token"
    assert "Expires in 24 hours" in msg["html"]
    assert admin.ADMIN_RESET_LINK_TTL == em.ADMIN_RESET_LINK_TTL


# ── every account email has a text part ──────────────────────────────────────

@pytest.mark.parametrize("case", EVERY, ids=_id)
def test_the_text_part_says_what_the_html_says(case):
    msg = _sent(case[0], *case[1], **case[2])
    assert msg.get("text"), f"{_id(case)} has no text part"
    for url in re.findall(r'<a [^>]*href="(https?://[^"]+)"', msg["html"]):
        if "/app/help" in url or url.startswith("mailto"):
            continue
        assert url.replace("&amp;", "&") in msg["text"], f"{_id(case)}: {url} missing from the text part"
    assert em.PLATFORM_POSTAL_ADDRESS in msg["text"]


# ── the schedule-failure notice (worker) ─────────────────────────────────────

def _notice(**kw):
    from worker import tasks
    args = dict(schedule_name="Monthly Irvine Snapshot", area="Irvine", brief_error="no data",
                active=True, consecutive_failures=1, schedule_url="https://x.test/app/schedules")
    args.update(kw)
    subject, content, _ = tasks._failure_notice(**args)
    return subject + content, tasks


def test_the_failure_notice_promises_no_retry():
    text, _ = _notice()
    assert "won&rsquo;t be re-sent" in text
    for wrong in ("try again", "retry", "within the hour"):
        assert wrong not in text.lower()


def test_the_failure_notice_counts_down_to_the_auto_pause():
    text, tasks = _notice(active=True, consecutive_failures=1)
    left = tasks.AUTO_PAUSE_AFTER - 1
    assert f"fails {left} more times in a row, it pauses itself" in text


def test_the_failure_notice_says_when_this_failure_paused_it():
    text, tasks = _notice(active=False, consecutive_failures=3)
    assert "so it has paused itself" in text
    assert "still on" not in text
