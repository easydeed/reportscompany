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
    logo_url: Optional[str]
    primary_color: Optional[str]
    accent_color: Optional[str]
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
    
    if branding_row:
        # Branding configured - use it
        return Brand(
            display_name=branding_row[0],
            logo_url=branding_row[1],
            primary_color=branding_row[2] or DEFAULT_PRIMARY,
            accent_color=branding_row[3] or DEFAULT_ACCENT,
            rep_photo_url=branding_row[4],
            contact_line1=branding_row[5],
            contact_line2=branding_row[6],
            website_url=branding_row[7],
        )
    
    # No branding configured
    if acc_type == 'INDUSTRY_AFFILIATE' or sponsor_id:
        # Affiliate without branding config, or sponsored agent
        # Use account name as brand
        if sponsor_id and branding_account_id == sponsor_id:
            # Get sponsor account name
            cur.execute("""
                SELECT name FROM accounts WHERE id = %s::uuid
            """, (sponsor_id,))
            sponsor_row = cur.fetchone()
            sponsor_name = sponsor_row[0] if sponsor_row else acc_name
            
            return Brand(
                display_name=sponsor_name,
                logo_url=None,
                primary_color=DEFAULT_PRIMARY,
                accent_color=DEFAULT_ACCENT,
                rep_photo_url=None,
                contact_line1=None,
                contact_line2=None,
                website_url=None,
            )
        else:
            # Affiliate using own name
            return Brand(
                display_name=acc_name,
                logo_url=None,
                primary_color=DEFAULT_PRIMARY,
                accent_color=DEFAULT_ACCENT,
                rep_photo_url=None,
                contact_line1=None,
                contact_line2=None,
                website_url=None,
            )
    
    # Unsponsored REGULAR account → TrendyReports default
    return _get_default_brand()


def _get_default_brand() -> Brand:
    """Returns default TrendyReports branding."""
    return Brand(
        display_name="TrendyReports",
        logo_url=None,  # Could add TrendyReports logo URL here if hosted
        primary_color=DEFAULT_PRIMARY,
        accent_color=DEFAULT_ACCENT,
        rep_photo_url=None,
        contact_line1=None,
        contact_line2=None,
        website_url=None,
    )


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

