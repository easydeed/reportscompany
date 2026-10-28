"""The account emails' shell (Design, 5th package), with the current wording.

What the change claims, each pinned:

  * every account email renders in the shell, light AND dark, readable in both
    (measured by pixel in Chromium, as the market email is);
  * every typed name is escaped (D-296);
  * the footer carries our address, never the one in Design's mocks;
  * the worker's copy of the shell (schedule-failure notice) is the API's copy.

The wording is not Design's yet, by owner decision: their copy contradicts
decisions already made, and comes in when it is corrected.
"""
import ast
import importlib.util
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "apps/worker/src"))
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")

from api.services import email as em  # noqa: E402

API_SRC = ROOT / "apps/api/src/api/services/email.py"
WORKER_SRC = ROOT / "apps/worker/src/worker/email/transactional.py"
MOCK_ADDRESSES = ("Jamboree", "92612")

#: (function, kwargs) for every account email the API sends.
CALLS = [
    ("send_verification_email", dict(email="a@x.test", user_name="Dana Ortiz", verification_token="t")),
    ("send_invite_email", dict(email="a@x.test", inviter_name="Sam Lee", company_name="Pacific Title",
                               invite_token="t", invitee_first_name="Dana")),
    ("send_password_reset_email", dict(email="a@x.test", user_name="Dana Ortiz", reset_token="t")),
    ("send_limit_warning_email", dict(email="a@x.test", first_name="Dana", count=4, limit=5)),
    ("send_limit_reached_email", dict(email="a@x.test", first_name="Dana", limit=5)),
    ("send_affiliate_welcome_email", dict(to_email="a@x.test", first_name="Dana")),
    ("send_sponsored_agent_welcome_email", dict(to_email="a@x.test", first_name="Dana",
                                                affiliate_company_name="Pacific Title")),
    ("send_regular_agent_welcome_email", dict(to_email="a@x.test", first_name="Dana")),
    ("send_company_admin_welcome_email", dict(to_email="a@x.test", first_name="Dana", company_name="Pacific Title")),
    ("send_rep_welcome_email", dict(to_email="a@x.test", first_name="Dana", company_name="Pacific Title")),
    ("send_rep_change_notice_email", dict(email="a@x.test", first_name="Dana", company_name="Pacific Title",
                                          new_rep_name="Ben Carter", new_rep_email="ben@x.test")),
] + [
    ("send_role_invite_email", dict(email="a@x.test", inviter_name="Sam Lee", company_name="Pacific Title",
                                    invite_token="t", invitee_first_name="Dana", role=role))
    for role in ("company_admin", "affiliate_admin", "title_rep", "sponsored_agent")
]

#: The fields a person types, per function.
TYPED = {"user_name", "inviter_name", "company_name", "invitee_first_name", "first_name",
         "affiliate_company_name", "new_rep_name"}
HOSTILE = '<img src=x onerror="alert(1)">'


def _render(name, kw):
    sent = {}
    with patch.object(em.email_service, "send_email_sync", lambda **p: sent.update(p) or {"ok": True}):
        getattr(em, name)(**kw)
    return sent["html"]


def _id(call):
    return call[0] + (":" + call[1]["role"] if "role" in call[1] else "")


@pytest.mark.parametrize("call", CALLS, ids=_id)
def test_every_account_email_is_in_the_shell_with_our_address(call):
    html = _render(*call)
    assert '<meta name="color-scheme" content="light dark">' in html
    assert "light only" not in html
    assert em.PLATFORM_POSTAL_ADDRESS in html
    for wrong in MOCK_ADDRESSES:
        assert wrong not in html
    assert "/app/help" in html


@pytest.mark.parametrize("call", CALLS, ids=_id)
def test_every_typed_name_is_escaped(call):
    """D-296: names typed by admins and invitees went into the markup raw."""
    name, kw = call
    hostile = {k: (HOSTILE if k in TYPED else v) for k, v in kw.items()}
    html = _render(name, hostile)
    assert "<img src=x" not in html, f"{_id(call)}: a typed name reached the HTML unescaped"


def test_the_platform_address_is_the_workers():
    """The API and the worker each carry the constant; they cannot disagree."""
    worker = (ROOT / "apps/worker/src/worker/email/template.py").read_text()
    assert f'or "{em.PLATFORM_POSTAL_ADDRESS}"' in worker


# ── the worker's mirror ────────────────────────────────────────────────────

SHARED = ("_FONT", "_e", "_row", "_h1", "_p", "_note", "_link", "_checklist", "_TONES",
          "_callout", "_cta_button", "_email_base")


def _defs(path):
    out = {}
    for node in ast.parse(path.read_text()).body:
        if isinstance(node, ast.FunctionDef):
            out[node.name] = ast.unparse(node)
        elif isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name):
            out[node.targets[0].id] = ast.unparse(node)
    return out


@pytest.mark.parametrize("name", SHARED)
def test_the_worker_shell_is_the_api_shell(name):
    api, worker = _defs(API_SRC), _defs(WORKER_SRC)
    assert name in api and name in worker, name
    assert api[name] == worker[name], (
        f"{name} differs between services/email.py and worker/email/transactional.py. "
        f"The worker cannot import the API, so the shell is mirrored; change both.")


def test_the_failure_notice_is_built_from_the_shell():
    tasks = (ROOT / "apps/worker/src/worker/tasks.py").read_text()
    i = tasks.index("def _send_failure_notification(")
    body = tasks[i:tasks.index("\ndef ", i + 10)]
    assert "_email_base(" in body and "light only" not in body
    assert "_e(brief_error)" in body, "the raw error text is not escaped"


# ── contrast, both schemes, by pixel ───────────────────────────────────────

def _pixel():
    spec = importlib.util.spec_from_file_location(
        "_measure_contrast_by_pixel", ROOT / "scripts/measure_contrast_by_pixel.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _measure(docs, scheme):
    if shutil.which("node") is None or subprocess.run(
            ["node", "-e", "require('playwright'); require('pngjs')"],
            cwd=str(ROOT), capture_output=True).returncode != 0:
        if os.environ.get("PDF_CONTRAST_REQUIRE_BROWSER") == "1":
            pytest.fail("the account-email contrast gate cannot run: no browser")
        pytest.skip("no browser")
    pixel = _pixel()
    return pixel.score(pixel.measure_docs(docs, scheme=scheme, width=680))


def _corpus():
    docs = {_id(c).replace(":", "__"): _render(*c) for c in CALLS}
    from worker.email import transactional as t
    docs["schedule_failed"] = t._email_base(
        t._h1("Hi Dana,") + t._p("Your scheduled report failed to generate.")
        + t._callout("Error details", "red") + t._cta_button("https://x.test", "View Schedules")
        + t._note("This is an automated notification from TrendyReports."))
    return docs


@pytest.mark.parametrize("scheme", ["light", "dark"])
def test_every_account_email_is_readable(scheme):
    rows = _measure(_corpus(), scheme)
    assert len(rows) > 150, "the measurement found almost no text"
    fails = [r for r in rows if r["ratio"] < r["needs"] and not r["unmeasurable"]]
    assert not fails, "\n".join(
        f"{r['ratio']:.2f}:1 {r['doc']} {r['selector'][:30]} {r['fg_hex']} on {r['bg_hex']} {r['text'][:30]!r}"
        for r in fails[:30])


def test_the_dark_gate_sees_unclassed_body_text(monkeypatch):
    """POSITIVE CONTROL: body text without its class is what the old content
    would have been in this shell — dark on dark. The gate must report it."""
    monkeypatch.setattr(em, "_p", lambda t: em._row(
        f'<p style="margin:0;font-size:15.5px;color:#334155;">{t}</p>'))
    html = _render(*CALLS[0])
    rows = _measure({"x": html}, "dark")
    assert any(r["ratio"] < r["needs"] for r in rows)
