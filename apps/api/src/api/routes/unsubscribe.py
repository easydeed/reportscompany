from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr
import hmac
import hashlib
import logging
import os
from ..db import db_conn

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1")

# Secret for HMAC token generation/validation.
# MUST match EMAIL_UNSUB_SECRET in the worker (apps/worker/src/worker/email/send.py).
# The worker SIGNS the token; this module VERIFIES it. If the two values differ,
# every unsubscribe link a recipient clicks returns 400 and nobody can opt out.
#
# DO NOT "fix" the dev fallback by making it equal to the worker's fallback.
# The two defaults differ deliberately. If they matched, an environment that
# forgot to set EMAIL_UNSUB_SECRET would appear to work while signing with a
# secret published in this repository — anyone could then forge a token and
# suppress delivery for any address on any account. Mismatched defaults fail
# closed; matched defaults fail open. The correct fix for an unset secret is to
# set it, which is what the critical log below tells you to do.
EMAIL_UNSUB_SECRET = os.getenv("EMAIL_UNSUB_SECRET")
if not EMAIL_UNSUB_SECRET:
    logger.critical(
        "EMAIL_UNSUB_SECRET not set (ENVIRONMENT=%s) — falling back to a dev "
        "default. It will NOT match the worker's signing secret, so every "
        "unsubscribe link will return 400 'Invalid unsubscribe token' and no "
        "recipient will be able to opt out. Set EMAIL_UNSUB_SECRET on this "
        "service to the same value as the worker service, then restart.",
        os.getenv("ENVIRONMENT", "unset"),
    )
    EMAIL_UNSUB_SECRET = "dev-unsubscribe-secret-change-in-prod"


# ====== Schemas ======
class UnsubscribeRequest(BaseModel):
    email: EmailStr
    token: str
    reason: str = "user_request"


# ====== Helpers ======
def generate_unsubscribe_token(account_id: str, email: str) -> str:
    """
    Generate HMAC token for unsubscribe links.
    Format: HMAC-SHA256(account_id:email, secret)
    MUST match the format in worker/email/send.py
    """
    message = f"{account_id}:{email}"
    return hmac.new(
        EMAIL_UNSUB_SECRET.encode(),
        message.encode(),
        hashlib.sha256
    ).hexdigest()


def verify_unsubscribe_token(account_id: str, email: str, token: str) -> bool:
    """
    Verify HMAC token matches account_id:email.
    """
    expected_token = generate_unsubscribe_token(account_id, email)
    return hmac.compare_digest(expected_token, token)


def _suppress(email: str, token: str, reason: str) -> str:
    """
    Resolve the account for `email`, verify `token` against it, and record a
    suppression. Shared by the link endpoint and the RFC 8058 one-click
    endpoint so there is exactly ONE implementation of the security check.

    Returns a short human-readable outcome. Raises HTTPException(400) when the
    token does not verify.
    """
    with db_conn() as conn:
        cur = conn.cursor()

        # Find account_id from schedules that contain this email
        cur.execute("""
            SELECT DISTINCT account_id::text
            FROM schedules
            WHERE %s = ANY(recipients)
            LIMIT 1
        """, (email,))

        row = cur.fetchone()
        if not row:
            # Email not found in any schedules - still return success (idempotent)
            return "Email unsubscribed"

        account_id = row[0]

        # Verify token
        if not verify_unsubscribe_token(account_id, email, token):
            raise HTTPException(
                status_code=400,
                detail="Invalid unsubscribe token"
            )

        # Insert into suppressions (idempotent due to UNIQUE constraint)
        cur.execute("""
            INSERT INTO email_suppressions (account_id, email, reason)
            VALUES (%s::uuid, %s, %s)
            ON CONFLICT (account_id, email) DO NOTHING
        """, (account_id, email, reason))

        conn.commit()

        return "Email unsubscribed successfully"


# ====== Routes ======
@router.post("/email/unsubscribe", status_code=status.HTTP_200_OK)
def unsubscribe_email(payload: UnsubscribeRequest):
    """
    Unsubscribe an email address from all schedules.

    Token format: HMAC-SHA256(email:account_id, secret)

    This endpoint does NOT require authentication - it uses the HMAC token
    to verify the unsubscribe request came from a legitimate email link.
    """
    return {"message": _suppress(payload.email, payload.token, payload.reason)}


@router.post("/email/unsubscribe/one-click", status_code=status.HTTP_200_OK)
def unsubscribe_one_click(email: EmailStr, token: str):
    """
    RFC 8058 one-click unsubscribe. The caller is the recipient's mail provider,
    not a person — this is what Gmail and Yahoo invoke behind the native
    "Unsubscribe" control next to the sender name.

    The credential lives entirely in the query string because that is the only
    place a mail provider will carry it: providers send a fixed
    `List-Unsubscribe=One-Click` form body, never our JSON shape, and they do
    not authenticate. The request body is deliberately ignored.

    POST ONLY, and that is load-bearing. Registering no GET means a GET returns
    405. Security scanners, link prefetchers and corporate mail gateways
    routinely issue a GET against every URL in a message, including the one in
    List-Unsubscribe. A GET-reachable one-click endpoint would silently
    unsubscribe people who never clicked anything, and nothing in the request
    would distinguish that from a genuine opt-out. RFC 8058 mandates POST for
    exactly this reason. Do not add a GET handler.

    WHY AN UNAUTHENTICATED POST IS SAFE HERE — read before changing anything
    upstream of it. This endpoint suppresses delivery for whatever address the
    caller names, and its only credential is `token`. That is acceptable solely
    because the token is an HMAC-SHA256 over "account_id:email" keyed on a
    secret held by the server and never published. The dependency chain:

      * apps/worker/src/worker/email/send.py signs with EMAIL_UNSUB_SECRET.
      * This module verifies with the same variable, and its dev fallback is
        deliberately DIFFERENT from the worker's (see the top of this file).
        Mismatched fallbacks fail closed.
      * If those two fallbacks were ever made equal, an environment missing
        EMAIL_UNSUB_SECRET would sign with a constant published in this
        repository. Because the account is resolved server-side from the email
        alone, anyone could then forge a token — and this endpoint would turn
        that into a one-request, no-click mass-suppression API that mail
        providers themselves can be induced to call.
      * apps/worker/tests/test_unsubscribe_token_roundtrip.py asserts those two
        fallbacks remain different, and that this route stays POST-only. Those
        assertions are what keep this route safe; they are not tidiness.
    """
    _suppress(email, token, "one_click")
    return {"message": "Email unsubscribed"}


@router.get("/email/unsubscribe/token")
def get_unsubscribe_token(email: str, account_id: str):
    """
    Generate an unsubscribe token for testing.
    
    WARNING: This endpoint should be disabled in production or require admin auth.
    It's provided for development/testing purposes only.
    """
    if os.getenv("ENVIRONMENT", "dev") == "production":
        raise HTTPException(status_code=404, detail="Not found")
    
    token = generate_unsubscribe_token(account_id, email)
    
    return {
        "email": email,
        "account_id": account_id,
        "token": token,
        "unsubscribe_url": f"/v1/email/unsubscribe?email={email}&token={token}"
    }

