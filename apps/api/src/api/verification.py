"""
Email verification, enforced where it means something.

D-019
-----
`POST /v1/auth/register` creates the user with `email_verified = false`, mails a
verification link, and then nothing anywhere reads the column. Logging in works.
Every authenticated surface works. The verification email is decorative.

The decision (Jerry, 2026-09-17) is to enforce on SENDING, not on login:

    an unverified account can log in, build and preview;
    it cannot send, and it cannot set up something that will send later.

That is the narrow rule that matches the harm. Gating login punishes the typo
victim by locking them out of an account they already paid attention to; gating
sending is what stops the platform putting mail into strangers' inboxes over a
return address nobody has confirmed. It also keeps the product usable during the
minute between signing up and clicking the link, which is when most people look
around.

WHOSE VERIFICATION — THE ACCOUNT'S, NOT THE REQUEST'S
-----------------------------------------------------
The check asks whether the ACCOUNT has any active user with a verified address,
not whether the calling user is verified. Three reasons, in order of how much
they matter:

1. **Not every authenticated request has a user.** `AuthContextMiddleware`
   resolves `request.state.user` only on the JWT path (authn.py:145). API-key
   callers and the `X-Demo-Account` fallback set `account_id` and no user at
   all. A per-user rule would have to invent an answer for those, and both
   available answers are wrong: deny, and API keys stop working; allow, and the
   gate is bypassable by authenticating differently.

2. **Sending is account-scoped.** The recipients, the branding, the plan
   quota and the `email_log` row are all keyed on the account. The verification
   fact belongs on the same object as the thing being gated.

3. **It is the correct answer for a shared account.** `accept_invite`
   (auth.py:466) sets `email_verified = TRUE` — clicking the invite link *is*
   the proof — so an invited member arrives verified. A company whose owner is
   verified should not lose sending because a second seat is mid-signup.

For a self-registered account the two readings coincide exactly: `register`
(auth.py:270-290) creates a fresh account holding exactly one user, so "the
account has a verified user" is "the registrant clicked the link".

FAIL CLOSED, DELIBERATELY
-------------------------
An account with no active users is NOT verified. So is an account whose users
all sit at `email_verified = false`. And a database error raises rather than
being swallowed — a check that cannot run must not decide "send it". The cost
of failing closed is a refused send that says why; the cost of failing open is
the thing this file exists to prevent.

THE REFUSAL IS RECORDED
-----------------------
`block_unverified_send` writes an `email_log` row before it raises. #61's
`duplicate_suppressed` set the precedent and the reason: a send that does not
happen must leave something behind saying why, or the only difference between
"we refused" and "it silently vanished" is a log line nobody will read at the
time it matters.

That write goes in its OWN transaction, which is not an accident — see the
comment on `_record_refusal`.
"""
from typing import NamedTuple, Optional

import logging

from fastapi import HTTPException

from .db import db_conn, set_rls

logger = logging.getLogger(__name__)


# The machine-readable code on the 403. The frontend switches on this rather
# than on the prose, so the prose can change without breaking the banner.
UNVERIFIED_ERROR_CODE = "email_not_verified"

# Where the frontend sends the user to get another link. This endpoint already
# exists (auth.py:916) and is public, takes an email, and is deliberately
# non-committal about whether the address is registered.
RESEND_ENDPOINT = "/v1/auth/resend-verification"

# `email_log.status` for a send refused because the account is unverified.
#
# A distinct status rather than reusing 'failed': nothing was attempted, so a
# retry would not help, and 'failed' is the status whose whole meaning is "try
# again". It is also deliberately NOT in admin.py's email-count allowlist
# ('sent', 'sending', 'failed') — a refusal is not an email, and that file's
# allowlist exists precisely so a status added later cannot inflate the number.
BLOCKED_STATUS = "blocked_unverified"


def manual_emails(recipients) -> Optional[list]:
    """
    The literal addresses in a recipients list, for the `to_emails` column on a
    refusal row. None when there are none.

    Deliberately partial. A recipients list mixes literal addresses with
    references — `{"type":"contact","id":...}`, groups, sponsored agents — and
    those resolve to addresses only at send time, which for a refused send never
    happens. Putting the ids in a column called `to_emails` would make the row
    read like it names recipients it does not name. Recording the subset that
    genuinely is an address is the honest version; the refusal's `error` text
    carries the rest of the story.

    Accepts the shapes this codebase actually passes: pydantic models with an
    `.email`, plain dicts, and bare strings (the frontend sends manual
    recipients as bare strings — unified-wizard/index.tsx:281).
    """
    if not recipients:
        return None
    out = []
    for r in recipients:
        value = None
        if isinstance(r, str):
            value = r
        elif isinstance(r, dict):
            value = r.get("email")
        else:
            value = getattr(r, "email", None)
        if value and "@" in str(value):
            out.append(str(value))
    return out or None


class SenderVerification(NamedTuple):
    verified: bool
    # The address to offer a resend link for: the oldest unverified active user
    # on the account, which for a self-registered account is the registrant.
    # None when there is nobody to offer it to (no active users at all).
    resend_email: Optional[str]
    active_users: int


def sender_verification(cur, account_id: str) -> SenderVerification:
    """
    Does this account have anyone behind it who has confirmed their address?

    Reads only. Raises on a database error rather than returning a verdict it
    did not compute.
    """
    cur.execute(
        """
        SELECT
            COALESCE(bool_or(COALESCE(email_verified, FALSE)), FALSE) AS any_verified,
            (ARRAY_AGG(email ORDER BY created_at ASC NULLS LAST)
               FILTER (WHERE NOT COALESCE(email_verified, FALSE)))[1] AS resend_email,
            COUNT(*) AS active_users
        FROM users
        WHERE account_id = %s::uuid
          AND COALESCE(is_active, TRUE) = TRUE
        """,
        (account_id,),
    )
    row = cur.fetchone()
    if not row:
        # An aggregate query always returns one row, so this is unreachable
        # short of a driver fault. Treat it the way every other unknown here is
        # treated.
        return SenderVerification(False, None, 0)
    any_verified, resend_email, active_users = row
    return SenderVerification(
        verified=bool(any_verified),
        resend_email=resend_email,
        active_users=int(active_users or 0),
    )


def _record_refusal(
    account_id: str,
    action: str,
    reason: str,
    to_emails: Optional[list],
    schedule_id: Optional[str],
    report_id: Optional[str],
) -> None:
    """
    Write the refusal to `email_log`, in a transaction of its own.

    THE SEPARATE CONNECTION IS THE POINT, NOT AN OVERSIGHT.

    Callers are inside `with db_conn() as (conn, cur):`, which commits only on a
    clean exit (db.py:56-61). `block_unverified_send` raises an HTTPException on
    the very next line, so anything written on the caller's cursor leaves with
    the rollback and the refusal is never recorded — the exact failure this
    function exists to prevent, arriving through the transaction rather than
    through a missing INSERT.

    So: own connection, own RLS scope, explicit commit, then return and let the
    caller raise.

    Never fatal. If the record cannot be written the send is still refused; a
    logged error is worse than an unrecorded refusal but much better than an
    unverified send going out because the bookkeeping failed.
    """
    try:
        with db_conn() as (conn, cur):
            set_rls(cur, account_id)
            cur.execute(
                """
                INSERT INTO email_log
                    (account_id, schedule_id, report_id, provider,
                     to_emails, subject, response_code, error, status)
                VALUES
                    (%s::uuid, %s::uuid, %s::uuid, NULL,
                     %s, %s, NULL, %s, %s)
                """,
                (
                    account_id,
                    schedule_id,
                    report_id,
                    to_emails or None,
                    f"[refused] {action}",
                    reason,
                    BLOCKED_STATUS,
                ),
            )
            conn.commit()
    except Exception as e:  # noqa: BLE001 — see docstring
        logger.error(
            "Could not record an unverified-send refusal for account %s "
            "(action=%s): %s — the send was still refused",
            account_id, action, e, exc_info=True,
        )


def block_unverified_send(
    cur,
    account_id: str,
    *,
    action: str,
    to_emails: Optional[list] = None,
    schedule_id: Optional[str] = None,
    report_id: Optional[str] = None,
) -> None:
    """
    Refuse `action` unless the account has a verified address. Returns None when
    the account may send; raises 403 otherwise.

    `action` is a short human phrase naming what was refused ("send this
    report", "create a schedule"). It goes in the message the user reads and in
    the `email_log` subject, so it should read as the thing they just clicked.
    """
    state = sender_verification(cur, account_id)
    if state.verified:
        return

    if state.active_users == 0:
        reason = (
            "the account has no active user, so there is no confirmed address "
            "to send on behalf of"
        )
    else:
        reason = (
            "no user on this account has confirmed their email address "
            "(users.email_verified is false for all of them)"
        )

    _record_refusal(
        account_id=account_id,
        action=action,
        reason=reason,
        to_emails=to_emails,
        schedule_id=schedule_id,
        report_id=report_id,
    )

    message = (
        f"Confirm your email address before you {action}. "
        "We sent a link when you signed up — check your inbox, or have us send "
        "another."
    )
    if state.resend_email:
        message = (
            f"Confirm {state.resend_email} before you {action}. "
            "We sent a link when you signed up — check your inbox, or have us "
            "send another."
        )

    raise HTTPException(
        status_code=403,
        detail={
            "error": UNVERIFIED_ERROR_CODE,
            "message": message,
            "action": action,
            "email": state.resend_email,
            "resend_endpoint": RESEND_ENDPOINT,
        },
    )
