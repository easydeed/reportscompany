"""
Branding Service

Provides brand resolution logic for white-label output.
Determines which brand should appear on client-facing reports and emails.

Brand Resolution (simple):
  REGULAR accounts  → always use their OWN accounts-table branding.
                       No sponsor/affiliate fallback. NULL logos are fine.
  INDUSTRY_AFFILIATE / TITLE_COMPANY → use affiliate_branding table
                       (with optional company→rep inheritance).
"""

from typing import Optional, TypedDict


class Brand(TypedDict, total=False):
    """Brand configuration for white-label output."""
    display_name: str
    # PDF logos
    logo_url: Optional[str]              # PDF header (gradient bg - light/white logo)
    footer_logo_url: Optional[str]       # PDF footer (gray bg - dark/colored logo)
    # Email logos
    email_logo_url: Optional[str]        # Email header (gradient bg - light/white logo)
    email_footer_logo_url: Optional[str] # Email footer (light bg - dark/colored logo)
    # Colors
    primary_color: Optional[str]
    accent_color: Optional[str]
    # Contact
    rep_photo_url: Optional[str]
    contact_line1: Optional[str]
    contact_line2: Optional[str]
    website_url: Optional[str]


DEFAULT_PRIMARY = "#4F46E5"   # Indigo
DEFAULT_ACCENT  = "#1a1a1a"   # Near-black


def get_brand_for_account(cur, account_id: str) -> Brand:
    """
    Returns the brand that should appear on reports/emails for this account.

    REGULAR accounts (sponsored or not) always use their own branding from
    the accounts table. No sponsor fallback.

    INDUSTRY_AFFILIATE / TITLE_COMPANY use the affiliate_branding table
    (with company→rep inheritance if the rep hasn't overridden).
    """
    cur.execute("""
        SELECT id::text, name, account_type
        FROM accounts
        WHERE id = %s::uuid
    """, (account_id,))

    account_row = cur.fetchone()
    if not account_row:
        return _get_default_brand()

    acc_id, acc_name, acc_type = account_row

    # ── REGULAR agents (sponsored or not) — always own branding ──
    if acc_type == 'REGULAR':
        return _get_regular_user_brand(cur, acc_id, acc_name)

    # ── Affiliates / Title Companies — affiliate_branding table ──
    branding_account_id = acc_id
    branding_row = _fetch_affiliate_branding_row(cur, branding_account_id)

    if branding_row:
        return branding_row

    # Affiliate without branding config — use account name + defaults
    return Brand(
        display_name=acc_name,
        logo_url=None,
        email_logo_url=None,
        footer_logo_url=None,
        email_footer_logo_url=None,
        primary_color=DEFAULT_PRIMARY,
        accent_color=DEFAULT_ACCENT,
        rep_photo_url=None,
        contact_line1=None,
        contact_line2=None,
        website_url=None,
    )


def _fetch_affiliate_branding_row(cur, account_id: str) -> Optional[Brand]:
    """Query affiliate_branding for an account, handling schema variations."""
    query_version = "full"
    branding_row = None

    try:
        cur.execute("""
            SELECT brand_display_name, logo_url, email_logo_url, footer_logo_url,
                   email_footer_logo_url, primary_color, accent_color,
                   rep_photo_url, contact_line1, contact_line2, website_url
            FROM affiliate_branding
            WHERE account_id = %s::uuid
        """, (account_id,))
        branding_row = cur.fetchone()
    except Exception as e:
        err_str = str(e).lower()
        if "email_footer_logo_url" in err_str:
            query_version = "legacy"
        elif "footer_logo_url" in err_str or "email_logo_url" in err_str:
            query_version = "minimal"

        if query_version == "legacy":
            try:
                cur.execute("""
                    SELECT brand_display_name, logo_url, email_logo_url, footer_logo_url,
                           primary_color, accent_color, rep_photo_url,
                           contact_line1, contact_line2, website_url
                    FROM affiliate_branding
                    WHERE account_id = %s::uuid
                """, (account_id,))
                branding_row = cur.fetchone()
            except Exception:
                query_version = "minimal"

        if query_version == "minimal":
            try:
                cur.execute("""
                    SELECT brand_display_name, logo_url, primary_color, accent_color,
                           rep_photo_url, contact_line1, contact_line2, website_url
                    FROM affiliate_branding
                    WHERE account_id = %s::uuid
                """, (account_id,))
                branding_row = cur.fetchone()
            except Exception:
                pass

    if not branding_row:
        return None

    if query_version == "full":
        return Brand(
            display_name=branding_row[0],
            logo_url=branding_row[1],
            email_logo_url=branding_row[2],
            footer_logo_url=branding_row[3],
            email_footer_logo_url=branding_row[4],
            primary_color=branding_row[5] or DEFAULT_PRIMARY,
            accent_color=branding_row[6] or DEFAULT_ACCENT,
            rep_photo_url=branding_row[7],
            contact_line1=branding_row[8],
            contact_line2=branding_row[9],
            website_url=branding_row[10],
        )
    elif query_version == "legacy":
        return Brand(
            display_name=branding_row[0],
            logo_url=branding_row[1],
            email_logo_url=branding_row[2],
            footer_logo_url=branding_row[3],
            email_footer_logo_url=None,
            primary_color=branding_row[4] or DEFAULT_PRIMARY,
            accent_color=branding_row[5] or DEFAULT_ACCENT,
            rep_photo_url=branding_row[6],
            contact_line1=branding_row[7],
            contact_line2=branding_row[8],
            website_url=branding_row[9],
        )
    else:
        return Brand(
            display_name=branding_row[0],
            logo_url=branding_row[1],
            email_logo_url=None,
            footer_logo_url=None,
            email_footer_logo_url=None,
            primary_color=branding_row[2] or DEFAULT_PRIMARY,
            accent_color=branding_row[3] or DEFAULT_ACCENT,
            rep_photo_url=branding_row[4],
            contact_line1=branding_row[5],
            contact_line2=branding_row[6],
            website_url=branding_row[7],
        )


def _get_default_brand() -> Brand:
    """Returns default TrendyReports branding."""
    return Brand(
        display_name="TrendyReports",
        logo_url=None,
        email_logo_url=None,
        footer_logo_url=None,
        email_footer_logo_url=None,
        primary_color=DEFAULT_PRIMARY,
        accent_color=DEFAULT_ACCENT,
        rep_photo_url=None,
        contact_line1=None,
        contact_line2=None,
        website_url=None,
    )


def _get_regular_user_brand(cur, account_id: str, account_name: str) -> Brand:
    """
    Returns branding for ALL regular accounts (sponsored or not).

    Reads logos, colors, contact info from the accounts table.
    NULL logos are returned as-is (no logo on the report is fine).
    """
    # Get branding from accounts table + user's avatar
    try:
        cur.execute("""
            SELECT 
                a.name,
                a.logo_url,
                a.footer_logo_url,
                a.email_logo_url,
                a.email_footer_logo_url,
                a.primary_color,
                a.secondary_color,
                a.contact_line1,
                a.contact_line2,
                a.website_url,
                u.avatar_url
            FROM accounts a
            LEFT JOIN users u ON u.account_id = a.id
            WHERE a.id = %s::uuid
            LIMIT 1
        """, (account_id,))
        row = cur.fetchone()
        
        if row:
            return Brand(
                display_name=row[0] or account_name,
                logo_url=row[1],
                footer_logo_url=row[2],
                email_logo_url=row[3],
                email_footer_logo_url=row[4],
                primary_color=row[5] or DEFAULT_PRIMARY,
                accent_color=row[6] or DEFAULT_ACCENT,
                contact_line1=row[7],
                contact_line2=row[8],
                website_url=row[9],
                rep_photo_url=row[10],  # User's avatar_url as headshot
            )
    except Exception as e:
        print(f"⚠️  Error loading regular user brand: {e}")
    
    # Fallback to default
    return _get_default_brand()


def validate_brand_input(data: dict) -> tuple[bool, Optional[str]]:
    """
    Validates brand input from API requests.
    
    Returns:
        (is_valid, error_message)
    """
    # Validate brand_display_name
    if not data.get('brand_display_name') or not data['brand_display_name'].strip():
        return False, "brand_display_name is required and cannot be empty"
    
    # Validate hex colors if provided
    for color_field in ['primary_color', 'accent_color']:
        if data.get(color_field):
            color = data[color_field].strip()
            if color and not _is_valid_hex_color(color):
                return False, f"{color_field} must be a valid hex color (e.g., #7C3AED)"
    
    return True, None


def _is_valid_hex_color(value: str) -> bool:
    """Check if value is a valid hex color."""
    if not value.startswith('#'):
        return False
    hex_part = value[1:]
    if len(hex_part) not in [3, 6]:
        return False
    try:
        int(hex_part, 16)
        return True
    except ValueError:
        return False

