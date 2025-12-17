"""
Phase 30: Affiliate Branding Service

Provides brand resolution logic for white-label output.
Determines which brand (TrendyReports, affiliate, or custom) should be used
for client-facing reports and emails.
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


# Default TrendyReports brand colors (Phase 26 palette)
DEFAULT_PRIMARY = "#7C3AED"   # Trendy violet
DEFAULT_ACCENT = "#F26B2B"    # Trendy coral


def get_brand_for_account(cur, account_id: str) -> Brand:
    """
    Returns the brand that should appear to CLIENTS for this account.
    
    Brand Resolution Logic:
    1. If account is REGULAR with sponsor_account_id:
       → Use sponsor's branding (affiliate white-label)
    2. If account is INDUSTRY_AFFILIATE:
       → Use its own branding (if configured)
    3. Else:
       → Fall back to TrendyReports default brand
    
    Args:
        cur: Database cursor
        account_id: The account generating the report/email
    
    Returns:
        Brand dict with display_name, colors, logo, contact info
    """
    # Load account info
    cur.execute("""
        SELECT 
            id::text,
            name,
            account_type,
            sponsor_account_id::text
        FROM accounts
        WHERE id = %s::uuid
    """, (account_id,))
    
    account_row = cur.fetchone()
    
    if not account_row:
        # Account not found - return default
        return _get_default_brand()
    
    acc_id, acc_name, acc_type, sponsor_id = account_row
    
    # Determine which account's branding to use
    if acc_type == 'REGULAR' and sponsor_id:
        # Sponsored agent → use affiliate's branding
        branding_account_id = sponsor_id
    else:
        # Affiliate or unsponsored → use own branding
        branding_account_id = acc_id
    
    # Look up branding configuration
    # Note: affiliate_branding table may not exist in all environments
    # Gracefully handle missing columns
    branding_row = None
    query_version = "full"  # full, legacy, minimal
    
    try:
        # Try full query with all columns (including email_footer_logo_url)
        cur.execute("""
            SELECT
                brand_display_name,
                logo_url,
                email_logo_url,
                footer_logo_url,
                email_footer_logo_url,
                primary_color,
                accent_color,
                rep_photo_url,
                contact_line1,
                contact_line2,
                website_url
            FROM affiliate_branding
            WHERE account_id = %s::uuid
        """, (branding_account_id,))
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
                    SELECT
                        brand_display_name,
                        logo_url,
                        email_logo_url,
                        footer_logo_url,
                        primary_color,
                        accent_color,
                        rep_photo_url,
                        contact_line1,
                        contact_line2,
                        website_url
                    FROM affiliate_branding
                    WHERE account_id = %s::uuid
                """, (branding_account_id,))
                branding_row = cur.fetchone()
            except Exception:
                query_version = "minimal"
        
        if query_version == "minimal":
            try:
                cur.execute("""
                    SELECT
                        brand_display_name,
                        logo_url,
                        primary_color,
                        accent_color,
                        rep_photo_url,
                        contact_line1,
                        contact_line2,
                        website_url
                    FROM affiliate_branding
                    WHERE account_id = %s::uuid
                """, (branding_account_id,))
                branding_row = cur.fetchone()
            except Exception:
                pass
    
    if branding_row:
        # Branding configured - use it
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
        else:  # minimal
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
    
    # No affiliate_branding row found
    if acc_type == 'INDUSTRY_AFFILIATE':
        # Affiliate without branding config - use account name as brand
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
    
    if sponsor_id:
        # Sponsored agent without sponsor branding - get sponsor name
        cur.execute("""
            SELECT name FROM accounts WHERE id = %s::uuid
        """, (sponsor_id,))
        sponsor_row = cur.fetchone()
        sponsor_name = sponsor_row[0] if sponsor_row else acc_name
        
        return Brand(
            display_name=sponsor_name,
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
    
    # Unsponsored REGULAR account → Use accounts table branding + user avatar (Option A)
    return _get_regular_user_brand(cur, acc_id, acc_name)


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
    Returns branding for un-sponsored regular users (Option A).
    
    Uses:
    - Branding fields from accounts table (logos, colors, contact info)
    - User's avatar_url as their headshot (rep_photo_url)
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
            LEFT JOIN users u ON u.active_account_id = a.id
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

