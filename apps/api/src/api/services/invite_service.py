"""
Shared invitation service for all user types.

Centralizes account + user + signup_token creation, token regeneration,
branding copy, and resend lookups. Route handlers stay thin.
"""

from __future__ import annotations

import logging
import secrets
from typing import Any, Dict, Optional

from ..settings import settings

logger = logging.getLogger(__name__)

TOKEN_EXPIRY_DAYS = 7

PLAN_FOR_ROLE = {
    "company_admin": "affiliate",
    "affiliate_admin": "affiliate",
    "title_rep": "sponsored_free",
    "sponsored_agent": "sponsored_free",
}

ACCOUNT_TYPE_FOR_ROLE = {
    "company_admin": "TITLE_COMPANY",
    "affiliate_admin": "INDUSTRY_AFFILIATE",
    "title_rep": "INDUSTRY_AFFILIATE",
    "sponsored_agent": "REGULAR",
}


def generate_unique_slug(cur: Any, base_name: str) -> str:
    """Generate a unique account slug (collision-safe)."""
    base = (
        base_name.lower()
        .replace(" ", "-")
        .replace(".", "")
        .replace(",", "")
        .replace("'", "")[:30]
    ) or "account"
    for _ in range(10):
        slug = f"{base}-{secrets.token_hex(4)}"
        cur.execute("SELECT 1 FROM accounts WHERE slug = %s", (slug,))
        if not cur.fetchone():
            return slug
    return f"{base}-{secrets.token_hex(8)}"


def create_invited_user(
    cur: Any,
    *,
    role: str,
    email: str,
    first_name: str,
    last_name: str = "",
    phone: Optional[str] = None,
    job_title: Optional[str] = None,
    company_name: Optional[str] = None,
    license_number: Optional[str] = None,
    account_name: Optional[str] = None,
    parent_account_id: Optional[str] = None,
    sponsor_account_id: Optional[str] = None,
    existing_account_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Create account (unless existing_account_id) + user + OWNER link + signup token.

    Use existing_account_id when the organization account already exists
    (e.g. admin inviting company admin onto a TITLE_COMPANY row).

    Raises ValueError if email is already registered.
    """
    email = email.strip().lower()
    cur.execute("SELECT id FROM users WHERE LOWER(email) = %s", (email,))
    if cur.fetchone():
        raise ValueError(f"A user with email {email} already exists")

    if existing_account_id:
        account_id = existing_account_id
    else:
        account_type = ACCOUNT_TYPE_FOR_ROLE.get(role, "REGULAR")
        plan_slug = PLAN_FOR_ROLE.get(role, "free")
        display_name = (account_name or f"{first_name} {last_name}".strip() or email.split("@")[0]).strip()
        slug = generate_unique_slug(cur, display_name)
        cur.execute(
            """
            INSERT INTO accounts (name, slug, account_type, plan_slug,
                                  parent_account_id, sponsor_account_id)
            VALUES (%s, %s, %s, %s, %s::uuid, %s::uuid)
            RETURNING id::text
            """,
            (
                display_name,
                slug,
                account_type,
                plan_slug,
                parent_account_id,
                sponsor_account_id,
            ),
        )
        account_id = cur.fetchone()[0]

    cur.execute(
        """
        INSERT INTO users (account_id, email, is_active, email_verified, role,
                           first_name, last_name, phone, job_title,
                           company_name, license_number)
        VALUES (%s::uuid, %s, true, false, 'member',
                %s, %s, %s, %s, %s, %s)
        RETURNING id::text
        """,
        (
            account_id,
            email,
            first_name.strip(),
            (last_name or "").strip(),
            phone,
            job_title,
            company_name,
            license_number,
        ),
    )
    user_id = cur.fetchone()[0]

    cur.execute(
        """
        INSERT INTO account_users (account_id, user_id, role)
        VALUES (%s::uuid, %s::uuid, 'OWNER')
        """,
        (account_id, user_id),
    )

    token = secrets.token_urlsafe(32)
    cur.execute(
        """
        INSERT INTO signup_tokens (token, user_id, account_id, expires_at)
        VALUES (%s, %s::uuid, %s::uuid, NOW() + INTERVAL '7 days')
        """,
        (token, user_id, account_id),
    )

    return {
        "account_id": account_id,
        "user_id": user_id,
        "token": token,
        "email": email,
        "invite_url": f"{settings.APP_BASE}/welcome?token={token}",
    }


def copy_branding_to_child(cur: Any, *, source_account_id: str, target_account_id: str) -> None:
    """Copy affiliate_branding from source to target; minimal row if source has none."""
    cur.execute("SAVEPOINT invite_branding_copy")
    try:
        cur.execute(
            """
            INSERT INTO affiliate_branding (
                account_id, brand_display_name, logo_url, email_logo_url,
                footer_logo_url, email_footer_logo_url,
                primary_color, accent_color, rep_photo_url,
                contact_line1, contact_line2, website_url,
                branding_override
            )
            SELECT
                %s::uuid, brand_display_name, logo_url, email_logo_url,
                footer_logo_url, email_footer_logo_url,
                primary_color, accent_color, NULL,
                contact_line1, contact_line2, website_url,
                FALSE
            FROM affiliate_branding
            WHERE account_id = %s::uuid
            """,
            (target_account_id, source_account_id),
        )
        cur.execute("RELEASE SAVEPOINT invite_branding_copy")
    except Exception as e:
        logger.warning("Branding copy with branding_override failed, retrying without: %s", e)
        cur.execute("ROLLBACK TO SAVEPOINT invite_branding_copy")
        cur.execute(
            """
            INSERT INTO affiliate_branding (
                account_id, brand_display_name, logo_url, email_logo_url,
                footer_logo_url, email_footer_logo_url,
                primary_color, accent_color, rep_photo_url,
                contact_line1, contact_line2, website_url
            )
            SELECT
                %s::uuid, brand_display_name, logo_url, email_logo_url,
                footer_logo_url, email_footer_logo_url,
                primary_color, accent_color, NULL,
                contact_line1, contact_line2, website_url
            FROM affiliate_branding
            WHERE account_id = %s::uuid
            """,
            (target_account_id, source_account_id),
        )
        cur.execute("RELEASE SAVEPOINT invite_branding_copy")

    cur.execute(
        "SELECT 1 FROM affiliate_branding WHERE account_id = %s::uuid",
        (target_account_id,),
    )
    if not cur.fetchone():
        try:
            cur.execute(
                """
                INSERT INTO affiliate_branding (account_id, branding_override)
                VALUES (%s::uuid, false)
                """,
                (target_account_id,),
            )
        except Exception:
            cur.execute(
                "INSERT INTO affiliate_branding (account_id) VALUES (%s::uuid)",
                (target_account_id,),
            )


def regenerate_invite_token(cur: Any, *, user_id: str, account_id: str) -> str:
    """Invalidate unused tokens and insert a new one with expiry."""
    cur.execute(
        """
        UPDATE signup_tokens SET used = TRUE
        WHERE user_id = %s::uuid AND used = FALSE
        """,
        (user_id,),
    )
    token = secrets.token_urlsafe(32)
    cur.execute(
        """
        INSERT INTO signup_tokens (token, user_id, account_id, expires_at)
        VALUES (%s, %s::uuid, %s::uuid, NOW() + INTERVAL '7 days')
        """,
        (token, user_id, account_id),
    )
    return token


def find_user_for_resend(
    cur: Any,
    *,
    email: str,
    sponsor_account_id: Optional[str] = None,
    parent_account_id: Optional[str] = None,
    account_type: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """
    Find an invited OWNER user for resend (case-insensitive email).
    Optionally scope by sponsor, parent, and/or account_type.
    """
    email = email.strip().lower()
    query = """
        SELECT u.id::text, u.email, u.email_verified,
               u.password_hash IS NOT NULL AS has_password,
               u.first_name, u.last_name,
               a.id::text AS account_id, a.name AS account_name
        FROM users u
        JOIN account_users au ON au.user_id = u.id AND au.role = 'OWNER'
        JOIN accounts a ON a.id = au.account_id
        WHERE LOWER(u.email) = %s
    """
    params: list[Any] = [email]
    if sponsor_account_id:
        query += " AND a.sponsor_account_id = %s::uuid"
        params.append(sponsor_account_id)
    if parent_account_id:
        query += " AND a.parent_account_id = %s::uuid"
        params.append(parent_account_id)
    if account_type:
        query += " AND a.account_type = %s"
        params.append(account_type)
    cur.execute(query, params)
    row = cur.fetchone()
    if not row:
        return None
    return {
        "user_id": row[0],
        "email": row[1],
        "email_verified": row[2],
        "has_password": row[3],
        "first_name": row[4] or "",
        "last_name": row[5] or "",
        "account_id": row[6],
        "account_name": row[7],
        "already_accepted": bool(row[2] and row[3]),
    }


def find_owner_pending_for_account(cur: Any, *, account_id: str) -> Optional[Dict[str, Any]]:
    """Return OWNER user row for an account (for admin resend flows)."""
    cur.execute(
        """
        SELECT u.id::text, u.email, u.email_verified,
               u.password_hash IS NOT NULL AS has_password,
               u.first_name, u.last_name,
               a.id::text AS account_id, a.name AS account_name
        FROM users u
        JOIN account_users au ON au.user_id = u.id AND au.role = 'OWNER'
        JOIN accounts a ON a.id = au.account_id
        WHERE a.id = %s::uuid
        LIMIT 1
        """,
        (account_id,),
    )
    row = cur.fetchone()
    if not row:
        return None
    return {
        "user_id": row[0],
        "email": row[1],
        "email_verified": row[2],
        "has_password": row[3],
        "first_name": row[4] or "",
        "last_name": row[5] or "",
        "account_id": row[6],
        "account_name": row[7],
        "already_accepted": bool(row[2] and row[3]),
    }


def get_inviter_context(
    cur: Any,
    *,
    account_id: str,
    inviter_user_id: Optional[str] = None,
) -> Dict[str, str]:
    """Display name for email: inviter + company/sponsor line."""
    cur.execute(
        """
        SELECT a.name, pa.name AS parent_name
        FROM accounts a
        LEFT JOIN accounts pa ON pa.id = a.parent_account_id
        WHERE a.id = %s::uuid
        """,
        (account_id,),
    )
    row = cur.fetchone()
    if row:
        company_name = (row[1] or row[0] or "TrendyReports").strip()
    else:
        company_name = "TrendyReports"

    inviter_name = "TrendyReports Admin"
    if inviter_user_id:
        cur.execute(
            """
            SELECT COALESCE(NULLIF(TRIM(first_name || ' ' || COALESCE(last_name, '')), ''), email)
            FROM users WHERE id = %s::uuid
            """,
            (inviter_user_id,),
        )
        urow = cur.fetchone()
        if urow and urow[0]:
            inviter_name = str(urow[0]).strip()

    return {"inviter_name": inviter_name, "company_name": company_name}


def infer_role_for_resend(cur: Any, *, user_id: str) -> str:
    """Pick email template role from user's primary account."""
    cur.execute(
        """
        SELECT a.account_type, a.parent_account_id IS NOT NULL AS has_parent,
               a.sponsor_account_id IS NOT NULL AS has_sponsor
        FROM users u
        JOIN accounts a ON a.id = u.account_id
        WHERE u.id = %s::uuid
        """,
        (user_id,),
    )
    row = cur.fetchone()
    if not row:
        return "sponsored_agent"
    acct_type, has_parent, has_sponsor = row[0], row[1], row[2]
    if acct_type == "TITLE_COMPANY":
        return "company_admin"
    if acct_type == "INDUSTRY_AFFILIATE" and has_parent:
        return "title_rep"
    if acct_type == "INDUSTRY_AFFILIATE":
        return "affiliate_admin"
    if acct_type == "REGULAR" and has_sponsor:
        return "sponsored_agent"
    return "sponsored_agent"
