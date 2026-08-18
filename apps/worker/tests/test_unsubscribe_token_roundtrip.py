"""
Regression tests for unsubscribe token generation and verification (U4).

These lock in the two defects that made unsubscribe non-functional in
production across 585 completed schedule runs:

  1. One message went to the whole recipient list carrying recipients[0]'s
     address and token, so every recipient after the first clicked a link that
     suppressed recipient #1 and left the clicker subscribed.
  2. The recipient's address was interpolated into the query string unencoded,
     so a plus-addressed recipient's '+' decoded as a space on the API side and
     the token never verified.

They also pin two properties that are easy to regress by "tidying":

  3. One message per recipient, so the To: header never discloses the list.
  4. Tokens signed with one secret do not verify under another. The worker's
     and API's dev fallbacks differ deliberately — see the comments at
     worker/email/send.py:16 and api/routes/unsubscribe.py:10. Making them
     equal would let any environment missing EMAIL_UNSUB_SECRET sign with a
     value published in this repository, and unsubscribe.py resolves account_id
     server-side from the email alone, so a forged token would suppress
     delivery for any address on any account.

Both modules read EMAIL_UNSUB_SECRET at *import* time, so each test loads them
fresh with a chosen secret rather than mutating a shared constant.

The worker's send.py imports two leaf modules this test does not exercise:
providers.sendgrid (an httpx client) and template (which pulls in
property_builder and Jinja). Both are stubbed so the test runs without the
worker's full dependency set — the stub for the template mirrors the single
href interpolation at template.py:2338. Everything under test — token
generation, URL construction, the send loop, and API-side verification — is
the real code.
"""
import hashlib
import hmac
import importlib
import os
import sys
import types
from urllib.parse import urlparse, parse_qs

import pytest

WEB_BASE = "https://reportscompany-web.vercel.app"
ACCOUNT_ID = "aaaaaaaa-1111-2222-3333-444444444444"
RECIPIENTS = ["alice@example.com", "bob@example.com", "carol+lists@example.com"]

_STUBBED = ("worker.email.template", "worker.email.providers.sendgrid")


def _install_stubs(sent):
    """Register stub leaf modules; return the sys.modules entries displaced."""
    saved = {name: sys.modules.get(name) for name in _STUBBED}

    sendgrid = types.ModuleType("worker.email.providers.sendgrid")

    def send_email(
        to_emails, subject, html_content, from_name=None, from_email=None, headers=None
    ):
        sent.append(
            {"to": list(to_emails), "html": html_content, "headers": headers or {}}
        )
        return (202, "Email sent successfully")

    sendgrid.send_email = send_email

    template = types.ModuleType("worker.email.template")
    # Mirrors template.py:2338 — the sole interpolation of unsubscribe_url.
    template.schedule_email_html = lambda **kw: (
        f'<html><body><a href="{kw["unsubscribe_url"]}">Unsubscribe</a></body></html>'
    )
    template.schedule_email_subject = lambda *a, **k: "Your Market Snapshot Report"

    sys.modules["worker.email.providers.sendgrid"] = sendgrid
    sys.modules["worker.email.template"] = template
    return saved


def _restore(saved):
    for name, module in saved.items():
        if module is None:
            sys.modules.pop(name, None)
        else:
            sys.modules[name] = module


@pytest.fixture
def worker_send(monkeypatch):
    """Load the real worker send module against a chosen secret.

    Yields (loader, sent) where loader(secret) returns the module and `sent`
    accumulates every message the stubbed provider was asked to deliver.
    """
    sent = []
    saved = _install_stubs(sent)

    def load(secret):
        monkeypatch.setenv("EMAIL_UNSUB_SECRET", secret)
        monkeypatch.setenv("WEB_BASE", WEB_BASE)
        sys.modules.pop("worker.email.send", None)
        return importlib.import_module("worker.email.send")

    try:
        yield load, sent
    finally:
        sys.modules.pop("worker.email.send", None)
        _restore(saved)


@pytest.fixture
def api_verifier(monkeypatch):
    """Load the real API unsubscribe module against a chosen secret."""

    def load(secret):
        monkeypatch.setenv("EMAIL_UNSUB_SECRET", secret)
        sys.modules.pop("api.routes.unsubscribe", None)
        return importlib.import_module("api.routes.unsubscribe")

    try:
        yield load
    finally:
        sys.modules.pop("api.routes.unsubscribe", None)


def _send(module, recipients):
    return module.send_schedule_email(
        account_id=ACCOUNT_ID,
        recipients=recipients,
        payload={
            "report_type": "market_snapshot",
            "city": "Anaheim",
            "pdf_url": "https://r2.example.com/report.pdf",
        },
    )


def _link_params(html):
    href = html.split('href="')[1].split('"')[0]
    query = parse_qs(urlparse(href).query)
    return query["email"][0], query["token"][0]


# ── 1. The worker signs, the API verifies ────────────────────────────────────

def test_worker_token_verifies_in_the_api(worker_send, api_verifier):
    """A token minted by the worker verifies in the API under a shared secret."""
    secret = "shared-secret-value-for-this-test"
    load_worker, _ = worker_send
    worker = load_worker(secret)
    api = api_verifier(secret)

    token = worker.generate_unsubscribe_token(ACCOUNT_ID, "alice@example.com")

    assert api.verify_unsubscribe_token(ACCOUNT_ID, "alice@example.com", token)


# ── 2. The multi-recipient defect ────────────────────────────────────────────

def test_each_recipient_can_only_unsubscribe_themselves(worker_send, api_verifier):
    """Every recipient's link carries THEIR address and a token that verifies
    for them and for nobody else.

    Fails before U1: one message went out carrying recipients[0]'s address, so
    bob and carol received a link that unsubscribed alice.
    """
    secret = "shared-secret-value-for-this-test"
    load_worker, sent = worker_send
    worker = load_worker(secret)
    api = api_verifier(secret)

    status, _ = _send(worker, RECIPIENTS)
    assert status == 202
    assert len(sent) == len(RECIPIENTS), (
        f"expected one message per recipient, got {len(sent)} for "
        f"{len(RECIPIENTS)} recipients"
    )

    for message in sent:
        recipient = message["to"][0]
        link_email, token = _link_params(message["html"])

        assert link_email == recipient, (
            f"{recipient} received a link addressed to {link_email}"
        )
        assert api.verify_unsubscribe_token(ACCOUNT_ID, recipient, token), (
            f"{recipient}'s own token did not verify for them"
        )

        for other in RECIPIENTS:
            if other == recipient:
                continue
            assert not api.verify_unsubscribe_token(ACCOUNT_ID, other, token), (
                f"{recipient}'s token also unsubscribes {other}"
            )


# ── 3. The plus-address defect ───────────────────────────────────────────────

@pytest.mark.parametrize(
    "recipient",
    [
        "carol+lists@example.com",
        "dave+trendyreports+2026@example.com",
        "erin.o'brien+re@example.com",
    ],
)
def test_plus_addressed_recipient_round_trips(worker_send, api_verifier, recipient):
    """A '+' in the local part survives the round trip.

    Fails before U1: the address was interpolated raw, so '+' decoded as a
    space on the API side and the token never verified.
    """
    secret = "shared-secret-value-for-this-test"
    load_worker, sent = worker_send
    worker = load_worker(secret)
    api = api_verifier(secret)

    _send(worker, [recipient])

    link_email, token = _link_params(sent[0]["html"])
    assert link_email == recipient, (
        f"address did not survive URL encoding: sent {recipient!r}, "
        f"link decoded to {link_email!r}"
    )
    assert api.verify_unsubscribe_token(ACCOUNT_ID, link_email, token)


# ── 4. The recipient list is not disclosed ───────────────────────────────────

def test_recipients_are_not_disclosed_to_each_other(worker_send):
    """Each message is addressed to exactly one recipient.

    Fails before U1: all recipients shared one personalizations[0].to array
    (providers/sendgrid.py:57-62), so every recipient saw the whole list.
    """
    load_worker, sent = worker_send
    worker = load_worker("shared-secret-value-for-this-test")

    _send(worker, RECIPIENTS)

    for message in sent:
        assert len(message["to"]) == 1, (
            f"message addressed to {len(message['to'])} recipients: {message['to']}"
        )
    assert sorted(m["to"][0] for m in sent) == sorted(RECIPIENTS)


# ── 5. Mismatched secrets fail closed ────────────────────────────────────────

def test_tokens_do_not_verify_under_a_different_secret(worker_send, api_verifier):
    """A token signed with one secret must not verify under another.

    This is the property that makes the differing dev fallbacks safe. If the
    two defaults were ever unified, an environment missing EMAIL_UNSUB_SECRET
    would sign with a value published in this repository and anyone could forge
    a suppression for any address. Do not "fix" this test by aligning secrets.
    """
    load_worker, _ = worker_send
    worker = load_worker("the-workers-secret")
    api = api_verifier("a-different-api-secret")

    token = worker.generate_unsubscribe_token(ACCOUNT_ID, "alice@example.com")

    assert not api.verify_unsubscribe_token(ACCOUNT_ID, "alice@example.com", token)


def test_worker_and_api_dev_fallbacks_are_not_equal():
    """The two dev fallbacks must stay different. See the module docstring."""
    worker_src = (
        "apps/worker/src/worker/email/send.py",
        "dev-only-secret-do-not-use-in-production",
    )
    api_src = (
        "apps/api/src/api/routes/unsubscribe.py",
        "dev-unsubscribe-secret-change-in-prod",
    )
    repo_root = os.path.join(os.path.dirname(__file__), "..", "..", "..")

    for path, expected in (worker_src, api_src):
        with open(os.path.join(repo_root, path), encoding="utf-8") as handle:
            assert expected in handle.read(), (
                f"{path} no longer contains its own dev fallback {expected!r}. "
                "If the fallbacks were unified, revert: matched defaults let a "
                "misconfigured environment sign with a public constant."
            )

    assert worker_src[1] != api_src[1]


# ── The signing contract itself ──────────────────────────────────────────────

def test_token_is_hmac_sha256_of_account_and_email(worker_send):
    """Pin the wire format both sides implement independently."""
    secret = "shared-secret-value-for-this-test"
    load_worker, _ = worker_send
    worker = load_worker(secret)

    expected = hmac.new(
        secret.encode(), f"{ACCOUNT_ID}:alice@example.com".encode(), hashlib.sha256
    ).hexdigest()

    assert worker.generate_unsubscribe_token(ACCOUNT_ID, "alice@example.com") == expected


# ── 6. RFC 8058 one-click headers (U5) ───────────────────────────────────────

def test_every_message_carries_one_click_headers(worker_send, api_verifier):
    """Each message carries List-Unsubscribe and List-Unsubscribe-Post, and the
    URL in the header is bound to that message's own recipient."""
    secret = "shared-secret-value-for-this-test"
    load_worker, sent = worker_send
    worker = load_worker(secret)
    api = api_verifier(secret)

    _send(worker, RECIPIENTS)

    for message in sent:
        recipient = message["to"][0]
        headers = message["headers"]

        assert headers.get("List-Unsubscribe-Post") == "List-Unsubscribe=One-Click"

        raw = headers["List-Unsubscribe"]
        assert raw.startswith("<") and raw.endswith(">"), (
            f"List-Unsubscribe must be a bracketed URI, got {raw!r}"
        )

        url = raw[1:-1]
        assert url.startswith(f"{WEB_BASE}/api/v1/email/unsubscribe/one-click?")

        query = parse_qs(urlparse(url).query)
        assert query["email"][0] == recipient
        assert api.verify_unsubscribe_token(ACCOUNT_ID, recipient, query["token"][0])

        for other in RECIPIENTS:
            if other != recipient:
                assert not api.verify_unsubscribe_token(
                    ACCOUNT_ID, other, query["token"][0]
                ), f"{recipient}'s one-click token also unsubscribes {other}"


def test_one_click_header_offers_no_mailto(worker_send):
    """https only. A mailto: alternative would route opt-outs to an inbox with
    no automation behind it — the silent-failure shape this branch removes."""
    load_worker, sent = worker_send
    worker = load_worker("shared-secret-value-for-this-test")

    _send(worker, ["alice@example.com"])

    header = sent[0]["headers"]["List-Unsubscribe"]
    assert "mailto:" not in header.lower()
    assert header.count("<") == 1, f"expected a single URI, got {header!r}"


def test_one_click_url_is_post_only_in_the_api():
    """The one-click path registers POST and nothing else, so a scanner's GET
    gets 405 rather than silently unsubscribing someone. See the route
    docstring — this assertion is the guard on that."""
    import importlib

    api = importlib.import_module("api.routes.unsubscribe")
    methods = {
        method
        for route in api.router.routes
        if getattr(route, "path", None) == "/v1/email/unsubscribe/one-click"
        for method in route.methods
    }

    assert methods, "one-click route is not registered"
    assert methods <= {"POST"}, (
        f"one-click must be POST-only; found {sorted(methods)}. A GET-reachable "
        "one-click endpoint unsubscribes people whose mail gateway prefetched "
        "the link."
    )
