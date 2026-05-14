"""
Brand resolution for TrendyReports accounts.

Centralizes the logic for determining which branding (logo, colors, display name)
an account should use, including parent-account inheritance for title reps.

This mirrors the worker's _resolve_email_brand logic in
apps/worker/src/worker/tasks.py — keep the two in sync. The worker remains the
runtime source of truth for PDF/email rendering; this service exposes the same
result to the API so the wizard preview and branding page match production.

Resolution order:
  1. INDUSTRY_AFFILIATE with parent_account_id:
       - If the rep's own affiliate_branding row has branding_override=true,
         use the rep's own row.
       - Otherwise inherit the parent's affiliate_branding row.
       - If the parent has no row, fall back to the rep's own row, then defaults.
  2. INDUSTRY_AFFILIATE / TITLE_COMPANY with no parent:
       - Use the account's own affiliate_branding row, then defaults.
  3. REGULAR (including sponsored agents):
       - Use the account's own branding ALWAYS. NEVER fall back to a sponsor's
         branding (see references/forbidden.md).
  4. Fallback to platform defaults if nothing is set.

Schema note:
  - `affiliate_branding` uses columns `accent_color` and `brand_display_name`.
  - `accounts` uses `secondary_color` and `name`.
  The resolver reads the affiliate row when an affiliate brand is involved and
  falls back to the accounts row for REGULAR accounts.
"""

from typing import Optional, TypedDict


# Platform defaults — must match worker DEFAULT_PRIMARY/DEFAULT_ACCENT and PDF
# templates. Keep these in sync if branding defaults change.
DEFAULT_PRIMARY = "#18235c"
DEFAULT_ACCENT = "#0d9488"
DEFAULT_DISPLAY_NAME = "TrendyReports"


class ResolvedBrand(TypedDict):
    """Resolved branding for an account."""
    logo_url: Optional[str]
    primary_color: str
    accent_color: str
    display_name: str
    source_account_id: str  # account_id that the brand actually came from
    source: str             # "self" | "parent" | "default"


def resolve_brand(cur, account_id: str) -> ResolvedBrand:
    """
    Resolve the effective branding for an account.

    Args:
        cur: psycopg2 cursor (positional-tuple cursor is fine — we read by name
             internally via cursor.description).
        account_id: UUID string of the account whose branding to resolve.

    Returns:
        ResolvedBrand dict.
    """
    cur.execute(
        """
        SELECT account_type, parent_account_id::text
        FROM accounts
        WHERE id = %s::uuid
        """,
        (account_id,),
    )
    acc = cur.fetchone()
    if not acc:
        return _default_brand(account_id)

    account_type = acc[0]
    parent_id = acc[1]

    own = _fetch_affiliate_branding(cur, account_id)

    if account_type == "INDUSTRY_AFFILIATE" and parent_id:
        # Rep with parent title company — inherit unless override is on.
        if own and own.get("branding_override"):
            return _format(own, account_id, "self")

        parent = _fetch_affiliate_branding(cur, parent_id)
        if parent:
            return _format(parent, parent_id, "parent")

        if own:
            return _format(own, account_id, "self")
        return _default_brand(account_id)

    if account_type in ("INDUSTRY_AFFILIATE", "TITLE_COMPANY"):
        # Affiliate with no parent (or the title company itself).
        if own:
            return _format(own, account_id, "self")
        return _default_brand(account_id)

    # REGULAR accounts (including sponsored agents).
    # Per forbidden.md: agents NEVER fall back to a sponsor's branding.
    regular = _fetch_account_branding(cur, account_id)
    if regular:
        return _format(regular, account_id, "self")
    return _default_brand(account_id)


def _fetch_affiliate_branding(cur, account_id: str) -> Optional[dict]:
    """Fetch the affiliate_branding row for an account, or None."""
    cur.execute(
        """
        SELECT
            logo_url,
            primary_color,
            accent_color,
            brand_display_name,
            branding_override
        FROM affiliate_branding
        WHERE account_id = %s::uuid
        """,
        (account_id,),
    )
    row = cur.fetchone()
    if not row:
        return None
    return {
        "logo_url": row[0],
        "primary_color": row[1],
        "accent_color": row[2],
        "display_name": row[3],
        "branding_override": row[4],
    }


def _fetch_account_branding(cur, account_id: str) -> Optional[dict]:
    """Fetch branding columns from the accounts table for REGULAR accounts."""
    cur.execute(
        """
        SELECT logo_url, primary_color, secondary_color, name
        FROM accounts
        WHERE id = %s::uuid
        """,
        (account_id,),
    )
    row = cur.fetchone()
    if not row:
        return None
    return {
        "logo_url": row[0],
        "primary_color": row[1],
        "accent_color": row[2],
        "display_name": row[3],
    }


def _format(row: dict, source_account_id: str, source: str) -> ResolvedBrand:
    return ResolvedBrand(
        logo_url=row.get("logo_url"),
        primary_color=row.get("primary_color") or DEFAULT_PRIMARY,
        accent_color=row.get("accent_color") or DEFAULT_ACCENT,
        display_name=row.get("display_name") or DEFAULT_DISPLAY_NAME,
        source_account_id=str(source_account_id),
        source=source,
    )


def _default_brand(account_id: str) -> ResolvedBrand:
    return ResolvedBrand(
        logo_url=None,
        primary_color=DEFAULT_PRIMARY,
        accent_color=DEFAULT_ACCENT,
        display_name=DEFAULT_DISPLAY_NAME,
        source_account_id=str(account_id),
        source="default",
    )
