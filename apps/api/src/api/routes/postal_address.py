"""An account's own postal address, for the footer of the mail it sends (D-079).

Jerry, 2026-10-30: per account, stored on `affiliate_branding.postal_address`.
An empty save clears it and never errors, and an account with none sends with
the platform address, attributed to TrendyReports — which is what the email
footer already does with a NULL (`worker.email.template`, D-060).

REGULAR ACCOUNTS HAVE NO BRANDING ROW, so the first save creates one, named
after the account. Nothing else reads it for them: both brand resolvers
(`services/brand_resolver.py`, `worker.tasks._resolve_email_brand`) branch on
account type and build a REGULAR account's brand from `accounts`, so the row
carries the address and changes nothing else about how that account looks.

WHO MAY SET IT. The account's OWNER — for a title company that is the company
admin (`deps.company.COMPANY_ADMIN_ROLE`, D-280). A rep who sends with the
company's brand sends with the company's address too, so there is nothing for
them to set; the GET says whose address it is instead.
"""
import re
from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, ConfigDict

from ..db import db_conn, set_rls
from ..deps.company import COMPANY_ADMIN_ROLE
from ..services.email import PLATFORM_POSTAL_ADDRESS

router = APIRouter(prefix="/v1")

#: Long enough for any real address on one line; a limit so the field cannot
#: carry a paragraph into every footer. Only an over-long value is refused —
#: an empty one is a clear, never an error (the D-059 trap).
MAX_LENGTH = 300


class PostalAddressIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    postal_address: Optional[str] = None


def clean(value: Optional[str]) -> Optional[str]:
    """One line, single-spaced, or None. Blank and whitespace-only are None."""
    text = re.sub(r"\s+", " ", value or "").strip()
    return text or None


def _state(request: Request) -> dict:
    user = getattr(request.state, "user", None)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    account_id = user.get("account_id") or getattr(request.state, "account_id", None)
    if not account_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    with db_conn() as (conn, cur):
        set_rls(cur, account_id)
        cur.execute(
            """
            SELECT a.account_type, a.parent_account_id::text,
                   (SELECT au.role FROM account_users au
                     WHERE au.account_id = a.id AND au.user_id = %s::uuid LIMIT 1),
                   ab.postal_address, COALESCE(ab.branding_override, false),
                   p.name, pb.postal_address
              FROM accounts a
              LEFT JOIN affiliate_branding ab ON ab.account_id = a.id
              LEFT JOIN accounts p ON p.id = a.parent_account_id
              LEFT JOIN affiliate_branding pb ON pb.account_id = a.parent_account_id
             WHERE a.id = %s::uuid
            """,
            (user.get("id"), account_id),
        )
        row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Account not found")
    acc_type, parent_id, role, own, override, parent_name, parent_address = row
    # A rep who has not set their own brand sends with the company's, address
    # included (`_resolve_email_brand`).
    inherits = acc_type == "INDUSTRY_AFFILIATE" and bool(parent_id) and not override
    return {
        "account_id": account_id,
        "own": own,
        "inherits": inherits,
        "company_name": parent_name if inherits else None,
        "company_address": parent_address if inherits else None,
        "can_edit": role == COMPANY_ADMIN_ROLE and not inherits,
    }


def _out(s: dict) -> dict:
    if s["inherits"]:
        in_use, source = s["company_address"], ("company" if s["company_address"] else "platform")
    else:
        in_use, source = s["own"], ("own" if s["own"] else "platform")
    return {
        "postal_address": s["own"],
        "can_edit": s["can_edit"],
        # What the footer of this account's mail carries today, and whose it is.
        "source": source,
        "in_use": in_use or PLATFORM_POSTAL_ADDRESS,
        "company_name": s["company_name"],
        "platform_address": PLATFORM_POSTAL_ADDRESS,
    }


@router.get("/account/postal-address")
def get_postal_address(request: Request):
    return _out(_state(request))


@router.put("/account/postal-address")
def put_postal_address(body: PostalAddressIn, request: Request):
    s = _state(request)
    if not s["can_edit"]:
        raise HTTPException(
            status_code=403,
            detail=("Your emails use your company's address; your company's admin sets it."
                    if s["inherits"] else "Only the account's owner can change its address."),
        )
    value = clean(body.postal_address)
    if value and len(value) > MAX_LENGTH:
        raise HTTPException(status_code=422, detail=f"Keep the address under {MAX_LENGTH} characters.")
    with db_conn() as (conn, cur):
        set_rls(cur, s["account_id"])
        # The first save creates the row; `brand_display_name` is NOT NULL, so
        # it is named after the account, as `PATCH /v1/company/branding` does.
        cur.execute(
            """
            INSERT INTO affiliate_branding (account_id, brand_display_name, postal_address, updated_at)
            VALUES (%s::uuid, COALESCE((SELECT name FROM accounts WHERE id = %s::uuid), ''), %s, NOW())
            ON CONFLICT (account_id) DO UPDATE
               SET postal_address = EXCLUDED.postal_address, updated_at = NOW()
            """,
            (s["account_id"], s["account_id"], value),
        )
        conn.commit()
    return _out({**s, "own": value})
