"""
D-148 — two welcome emails printed the literal text `{company}`.

Found while fixing D-147, in the same three lines. `send_rep_welcome_email`
builds its body as an f-string whose `{_step_row(...)}` calls take plain
string literals as arguments. A `{company}` inside one of those literals is
not in the outer f-string's expression scope — it is ordinary text — so every
title rep who accepted an invite was told their agents' reports would carry
"{company}'s branding".

`send_company_admin_welcome_email` has the same shape and was checked: its
step rows carry no placeholder, so it was not affected.

Asserting on the rendered HTML rather than on the source, because the defect
is that a brace survived to the reader.
"""
from unittest.mock import patch

from api.services import email as email_mod


def _render(fn, **kw):
    sent = {}

    def _spy(**payload):
        sent.update(payload)
        return {"id": "test"}

    with patch.object(email_mod.email_service, "send_email_sync", _spy):
        fn(**kw)
    return sent


def test_the_rep_welcome_names_the_company():
    sent = _render(
        email_mod.send_rep_welcome_email,
        to_email="rep@example.com",
        first_name="Dana",
        company_name="Pacific Title",
    )
    html = sent["html"]
    assert "{company}" not in html, "an unsubstituted placeholder reached the reader"
    assert "{name}" not in html
    assert html.count("Pacific Title") >= 3, (
        "the company name should appear in the intro and in both step rows "
        "that mention it"
    )


def test_the_rep_welcome_falls_back_when_no_company_is_known():
    """The fallback string is `your company`. It must interpolate too —
    a defect that only shows with a value set is half-tested."""
    sent = _render(
        email_mod.send_rep_welcome_email,
        to_email="rep@example.com",
        first_name="",
        company_name="",
    )
    assert "{company}" not in sent["html"]
    assert "your company" in sent["html"]
    assert "Welcome aboard, there!" in sent["html"]


def test_the_company_admin_welcome_has_no_stray_placeholders():
    sent = _render(
        email_mod.send_company_admin_welcome_email,
        to_email="admin@example.com",
        first_name="Sam",
        company_name="Pacific Title",
    )
    assert "{company}" not in sent["html"]
    assert "{name}" not in sent["html"]
