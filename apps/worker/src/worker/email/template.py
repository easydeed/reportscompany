"""HTML email template for scheduled report notifications.

V15: Premium V0-inspired redesign matching React email previews.
- BRANDED: Hero metric in tinted card with serif font (Georgia) and gold accent bar
- BRANDED: Section labels with accent bar prefix (V0 SectionLabel component)
- BRANDED: AI Insight paragraph with left border in brand color
- BRANDED: Quick Take callout in accent-colored card with $ icon
- BRANDED: CTA button area in tinted background container
- BRANDED: Agent footer with branded bg, serif name, pill contact buttons
- BRANDED: Core Indicators with accent dots and serif numbers
- LAYOUT: Property Types + Price Tiers side-by-side with progress bars
- LAYOUT: Gallery count badge with branded pill + line separator
- GALLERY: Brand-tinted detail badges (Bed/Bath/SF) and serif prices
- TABLE: Brand-colored header row with white text + summary stats
- NEW: KPI card helpers with trend indicators for analytics layouts
- NEW: Year-over-Year comparison table helper with brand header
- TYPOGRAPHY: Georgia serif for hero metrics, key numbers (premium feel)

V10: Corporate/Professional redesign for Market Snapshot.
- REMOVED: Emojis from Quick Take, preheaders, and CTAs
- REMOVED: "Conversation Starter" green callout box (too casual)
- REDESIGNED: Quick Take now a subtle italic insight line (no yellow box)
- REDESIGNED: Key Stats Bar - clean bordered cards instead of gradient
- REDESIGNED: Headline metric uses neutral dark color instead of brand color
- REFINED: Core Indicators, Property Types, Price Tiers - cleaner borders
- PROFESSIONAL: All language updated to be data-focused and corporate
- SINGLE CTA: "View Full Report" button using brand primary color

V8: Adaptive gallery layouts for professional appearance.
- 3, 6, 9 listings → 3-column grid
- 2, 4 listings → 2-column grid
- 1, 5, 7, 8, 10+ listings → Vertical list (image left, info right)

V4: PDF-aligned redesign - email now mirrors the PDF report structure.
- Title format "Market Snapshot – [Area]" (matches PDF header)
- Subline "Period: Last X days • Source: Live MLS Data"  
- Insight paragraph with 1-2 sentence market summary
- 4-metric Hero Row (Median Price, Closed Sales, DOM, MOI)
- Core Indicators section (New Listings, Pending, Sale-to-List)

V3: Professional styling refresh with enhanced Market Snapshot data.
- Table-based layout for maximum email client compatibility
- MSO/Outlook conditional comments for rounded buttons and circular photos
- VML fallback for Outlook gradient headers
- Dark mode support
- Mobile responsive (metrics stack on mobile)
- Full white-label branding support
"""
from typing import Dict, Optional, TypedDict, Tuple, List


class Brand(TypedDict, total=False):
    """Brand configuration for white-label emails."""
    display_name: str
    logo_url: Optional[str]
    email_logo_url: Optional[str]  # Separate logo for email headers (light version)
    primary_color: Optional[str]
    accent_color: Optional[str]
    rep_name: Optional[str]
    rep_title: Optional[str]
    rep_photo_url: Optional[str]
    rep_phone: Optional[str]
    rep_email: Optional[str]
    contact_line1: Optional[str]
    contact_line2: Optional[str]
    website_url: Optional[str]


# Report type display names and taglines
# V4: market_snapshot uses PDF-aligned structure with 4-metric hero + core indicators
REPORT_CONFIG = {
    "market_snapshot": {
        "label": "Market Snapshot",
        "tagline": None,  # V4: Uses "Market Snapshot – [Area]" instead of generic tagline
        "section": None,  # V4: No section label - structured sections instead
        "has_extra_stats": False,  # V4: MOI now in hero row
        "has_property_types": True,
        "has_price_tiers": True,
        "has_hero_4": True,  # V4: 4-metric hero row (Median, Closed, DOM, MOI)
        "has_core_indicators": True,  # V4: Core indicators section (New, Pending, CTL)
        "has_insight": True,  # V4: Insight paragraph
    },
    "new_listings": {
        "label": "New Listings",
        "tagline": None,  # V4: Uses PDF-aligned title
        "section": None,
        "has_extra_stats": False,
        "has_hero_4": True,  # V4: 4-metric hero row
        "has_insight": True,  # V4: Insight paragraph
    },
    "inventory": {
        "label": "Inventory Report",
        "tagline": None,  # V4: Uses PDF-aligned title
        "section": None,
        "has_extra_stats": False,
        "has_hero_4": True,  # V4: 4-metric hero row
        "has_insight": True,  # V4: Insight paragraph
        "has_listings_table": True,  # V5: Include listings table
    },
    "closed": {
        "label": "Closed Sales",
        "tagline": None,  # V4: Uses PDF-aligned title
        "section": None,
        "has_extra_stats": False,  # V4: Integrated into hero row
        "has_hero_4": True,  # V4: 4-metric hero row
        "has_insight": True,  # V4: Insight paragraph
        "has_listings_table": True,  # V6: Include listings table
    },
    "price_bands": {
        "label": "Price Analysis",
        "tagline": None,  # V4: Uses PDF-aligned title
        "section": None,
        "has_extra_stats": False,
        "has_price_bands": True,
        "has_hero_4": True,  # V4: 4-metric hero row
        "has_insight": True,  # V4: Insight paragraph
    },
    "open_houses": {
        "label": "Open Houses",
        "tagline": "Open This Weekend",
        "section": "Open Houses",
        "has_extra_stats": False,
    },
    "new_listings_gallery": {
        "label": "New Listings Gallery",
        "tagline": None,  # V6.1: Use report label in header for consistency
        "section": "New Listings",
        "has_extra_stats": False,
        "has_insight": True,  # V13: AI-powered insight for gallery emails
    },
    "featured_listings": {
        "label": "Featured Listings",
        "tagline": None,  # V6: Use report label in header for consistency
        "section": "Featured Properties",
        "has_extra_stats": False,
        "has_insight": True,  # V13: AI-powered insight for featured emails
    },
}


def _format_price(price: Optional[float]) -> str:
    """Format price for display."""
    if price is None:
        return "N/A"
    if price >= 1_000_000:
        # Format as millions, strip trailing zeros and decimal point
        formatted = f"${price / 1_000_000:.2f}".rstrip('0').rstrip('.')
        return f"{formatted}M"
    if price >= 1_000:
        return f"${price / 1_000:.0f}K"
    return f"${price:,.0f}"


def _format_price_clean(price: Optional[float]) -> str:
    """Format price for display - cleaner version."""
    if price is None:
        return "N/A"
    if price >= 1_000_000:
        m = price / 1_000_000
        if m == int(m):
            return f"${int(m)}M"
        return f"${m:.1f}M"
    if price >= 1_000:
        k = price / 1_000
        if k == int(k):
            return f"${int(k)}K"
        return f"${k:.0f}K"
    return f"${price:,.0f}"


def _format_number(value: Optional[int]) -> str:
    """Format number for display."""
    if value is None:
        return "N/A"
    return f"{value:,}"


def _format_percent(value: Optional[float]) -> str:
    """Format percentage for display."""
    if value is None:
        return "N/A"
    return f"{value:.1f}%"


# ============================================================================
# V16: LAYOUT-BASED EMAIL ARCHITECTURE
# Translated from V0 React designs in apps/web/app/email-templates/layouts/
# ============================================================================


# ---------------------------------------------------------------------------
# Phase 1: Shared Component Helpers
# ---------------------------------------------------------------------------

def _build_ai_narrative(insight_text: str) -> str:
    """Plain 16px narrative paragraph on white. Ref: V0 market-narrative.tsx"""
    if not insight_text:
        return ""
    return f'''
              <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="margin-bottom: 32px;">
                <tr>
                  <td>
                    <p style="margin: 0; font-size: 16px; line-height: 1.8; color: #1c1917;">
                      {insight_text}
                    </p>
                  </td>
                </tr>
              </table>'''


def _build_hero_stat(value: str, label: str, primary_color: str,
                     trend: str = None, trend_positive: bool = True) -> str:
    """56px Georgia serif hero stat, centered. Ref: V0 market-narrative.tsx"""
    trend_html = ""
    if trend:
        color = "#059669" if trend_positive else "#dc2626"
        arrow = "&#9650;" if trend_positive else "&#9660;"
        trend_html = f'''
                    <p style="margin: 8px 0 0; font-size: 13px; font-weight: 600; color: {color};">
                      <span style="display: inline-block; margin-right: 2px;">{arrow}</span> {trend}
                    </p>'''
    return f'''
              <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="margin-bottom: 32px;">
                <tr>
                  <td align="center" style="padding: 40px 20px;">
                    <p style="margin: 0 0 8px; font-family: Georgia, 'Times New Roman', serif; font-size: 56px; font-weight: 700; color: {primary_color}; line-height: 1; letter-spacing: -1px;">
                      {value}
                    </p>
                    <p style="margin: 0; font-size: 11px; font-weight: 600; color: #78716c; text-transform: uppercase; letter-spacing: 2px;">
                      {label}
                    </p>{trend_html}
                  </td>
                </tr>
              </table>'''


def _build_gallery_count(count: int, label: str, primary_color: str) -> str:
    """Branded pill badge + label + horizontal rule. Ref: V0 gallery-3x2.tsx"""
    return f'''
              <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="margin-bottom: 20px;">
                <tr>
                  <td>
                    <table role="presentation" cellpadding="0" cellspacing="0" width="100%">
                      <tr>
                        <td style="padding-right: 12px; vertical-align: middle;" width="28">
                          <table role="presentation" cellpadding="0" cellspacing="0">
                            <tr>
                              <td align="center" style="width: 28px; height: 28px; background-color: {primary_color}; color: #ffffff; font-size: 12px; font-weight: 700; border-radius: 50%; line-height: 28px;">
                                {count}
                              </td>
                            </tr>
                          </table>
                        </td>
                        <td style="vertical-align: middle; padding-right: 12px; white-space: nowrap;">
                          <span style="font-size: 14px; font-weight: 600; color: #1c1917;">{label}</span>
                        </td>
                        <td style="vertical-align: middle; width: 100%;">
                          <div style="height: 1px; background-color: #e7e5e4;"></div>
                        </td>
                      </tr>
                    </table>
                  </td>
                </tr>
              </table>'''


def _build_quick_take(text: str, accent_color: str) -> str:
    """Accent-colored callout with $ icon. Ref: V0 market-narrative.tsx"""
    if not text:
        return ""
    return f'''
              <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="margin-bottom: 28px;">
                <tr>
                  <td style="padding: 18px 20px; background-color: {accent_color}0F; border: 1px solid {accent_color}33; border-radius: 8px;">
                    <table role="presentation" cellpadding="0" cellspacing="0" width="100%">
                      <tr>
                        <td width="28" style="vertical-align: top; padding-right: 12px;">
                          <span style="font-size: 20px; color: {accent_color};">&#36;</span>
                        </td>
                        <td style="vertical-align: top;">
                          <p style="margin: 0; font-size: 14px; font-weight: 500; line-height: 1.6; color: #1c1917;">
                            {text}
                          </p>
                        </td>
                      </tr>
                    </table>
                  </td>
                </tr>
              </table>'''


def _build_cta(pdf_url: str, primary_color: str, cta_text: str = "View Full Report") -> str:
    """Tinted container with branded button + VML fallback. Ref: V0 market-narrative.tsx"""
    return f'''
              <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="margin-bottom: 28px;">
                <tr>
                  <td align="center" style="padding: 24px; background-color: {primary_color}0A; border-radius: 8px;">
                    <!--[if mso]>
                    <v:roundrect xmlns:v="urn:schemas-microsoft-com:vml" xmlns:w="urn:schemas-microsoft-com:office:word" href="{pdf_url}" style="height:48px;v-text-anchor:middle;width:220px;" arcsize="8%" stroke="f" fillcolor="{primary_color}">
                      <w:anchorlock/>
                      <center style="color:#ffffff;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Arial,sans-serif;font-size:14px;font-weight:600;">{cta_text}</center>
                    </v:roundrect>
                    <![endif]-->
                    <!--[if !mso]><!-->
                    <a href="{pdf_url}" target="_blank" style="display: inline-block; background-color: {primary_color}; color: #ffffff; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; font-size: 14px; font-weight: 600; text-decoration: none; padding: 14px 36px; border-radius: 8px; letter-spacing: 0.3px;">
                      {cta_text}
                    </a>
                    <!--<![endif]-->
                  </td>
                </tr>
              </table>'''


def _build_section_label(label: str, primary_color: str) -> str:
    """20x2px accent bar + uppercase branded label. Ref: V0 SectionLabel."""
    return f'''
              <table role="presentation" cellpadding="0" cellspacing="0" style="margin-bottom: 14px;">
                <tr>
                  <td style="width: 20px; padding-right: 8px; vertical-align: middle;">
                    <div style="width: 20px; height: 2px; background-color: {primary_color}; border-radius: 2px;"></div>
                  </td>
                  <td style="vertical-align: middle;">
                    <p style="margin: 0; font-size: 11px; font-weight: 700; color: {primary_color}; text-transform: uppercase; letter-spacing: 2px;">
                      {label}
                    </p>
                  </td>
                </tr>
              </table>'''


def _build_filter_blurb(filter_text: str, primary_color: str) -> str:
    """Optional report criteria callout."""
    if not filter_text:
        return ""
    return f'''
              <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="margin-bottom: 20px;">
                <tr>
                  <td style="padding: 12px 16px; background-color: {primary_color}08; border-radius: 8px; border-left: 3px solid {primary_color};">
                    <p style="margin: 0; font-size: 13px; line-height: 1.5; color: #44403c;">
                      <span style="font-weight: 600; color: {primary_color};">Report Criteria:</span> {filter_text}
                    </p>
                  </td>
                </tr>
              </table>'''


def _build_stacked_stats(stats: List[Tuple[str, str]]) -> str:
    """Full-width rows: label left, big serif number right. Ref: V0 market-narrative.tsx"""
    if not stats:
        return ""
    rows = ""
    for i, (label, value) in enumerate(stats):
        bg = "#ffffff" if i % 2 == 0 else "#fafaf9"
        border = "border-bottom: 1px solid #f5f5f4;" if i < len(stats) - 1 else ""
        rows += f'''
                      <tr>
                        <td style="padding: 16px 20px; background-color: {bg}; {border}">
                          <table role="presentation" cellpadding="0" cellspacing="0" width="100%">
                            <tr>
                              <td style="vertical-align: middle;">
                                <span style="font-size: 14px; color: #57534e;">{label}</span>
                              </td>
                              <td align="right" style="vertical-align: middle;">
                                <span style="font-family: Georgia, 'Times New Roman', serif; font-size: 24px; font-weight: 700; color: #1c1917;">{value}</span>
                              </td>
                            </tr>
                          </table>
                        </td>
                      </tr>'''
    return f'''
              <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="margin-bottom: 32px;">
                <tr>
                  <td>
                    <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="border: 1px solid #e7e5e4; border-radius: 12px; overflow: hidden;">
                      {rows}
                    </table>
                  </td>
                </tr>
              </table>'''


def _build_trend_stats(stats: List[Tuple[str, str, str, bool]], primary_color: str) -> str:
    """Stacked rows with trend indicators. Ref: V0 market-analytics.tsx
    stats: list of (label, value, trend_text, trend_positive) tuples"""
    if not stats:
        return ""
    rows = ""
    for i, (label, value, trend_text, positive) in enumerate(stats):
        bg = "#ffffff" if i % 2 == 0 else "#fafaf9"
        border = "border-bottom: 1px solid #f5f5f4;" if i < len(stats) - 1 else ""
        color = "#059669" if positive else "#dc2626"
        arrow = "&#9650;" if positive else "&#9660;"
        trend_html = f'<span style="font-size: 11px; font-weight: 600; color: {color}; margin-left: 12px;"><span style="margin-right: 2px;">{arrow}</span>{trend_text}</span>' if trend_text else ""
        rows += f'''
                      <tr>
                        <td style="padding: 16px 20px; background-color: {bg}; {border}">
                          <table role="presentation" cellpadding="0" cellspacing="0" width="100%">
                            <tr>
                              <td style="vertical-align: middle;">
                                <span style="font-size: 14px; color: #57534e;">{label}</span>
                              </td>
                              <td align="right" style="vertical-align: middle;">
                                <span style="font-family: Georgia, 'Times New Roman', serif; font-size: 24px; font-weight: 700; color: #1c1917;">{value}</span>
                                {trend_html}
                              </td>
                            </tr>
                          </table>
                        </td>
                      </tr>'''
    return f'''
              <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="margin-bottom: 32px;">
                <tr>
                  <td>
                    <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="border: 1px solid #e7e5e4; border-radius: 12px; overflow: hidden;">
                      {rows}
                    </table>
                  </td>
                </tr>
              </table>'''


def _build_branded_divider(primary_color: str, accent_color: str) -> str:
    """64px gradient bar between stacked cards. Ref: V0 single-stacked.tsx"""
    return f'''
              <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="margin: 16px 0;">
                <tr>
                  <td align="center">
                    <div style="width: 64px; height: 2px; background: linear-gradient(90deg, {primary_color}, {accent_color}); border-radius: 2px;"></div>
                  </td>
                </tr>
              </table>'''


def _build_yoy_comparison(last_year: List[Tuple[str, str]], this_year: List[Tuple[str, str]], primary_color: str) -> str:
    """Side-by-side Year-over-Year comparison. Ref: V0 market-analytics.tsx
    Each list: [(label, value), ...]"""
    if not last_year or not this_year:
        return ""
    ly_rows = ""
    for label, val in last_year:
        ly_rows += f'''
                            <tr>
                              <td style="padding: 8px 0;">
                                <p style="margin: 0; font-family: Georgia, 'Times New Roman', serif; font-size: 20px; font-weight: 700; color: #78716c;">{val}</p>
                                <p style="margin: 2px 0 0; font-size: 11px; color: #a8a29e;">{label}</p>
                              </td>
                            </tr>'''
    ty_rows = ""
    for label, val in this_year:
        ty_rows += f'''
                            <tr>
                              <td style="padding: 8px 0;">
                                <p style="margin: 0; font-family: Georgia, 'Times New Roman', serif; font-size: 20px; font-weight: 700; color: {primary_color};">{val}</p>
                                <p style="margin: 2px 0 0; font-size: 11px; color: #78716c;">{label}</p>
                              </td>
                            </tr>'''
    return f'''
              <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="margin-bottom: 32px;">
                <tr>
                  <td>
                    <p style="margin: 0 0 12px; font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 2px; color: #78716c;">Year-Over-Year Comparison</p>
                    <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="border: 1px solid #e7e5e4; border-radius: 12px; overflow: hidden;">
                      <tr>
                        <td width="50%" style="padding: 20px; background-color: #f5f5f4; border-right: 1px solid #e7e5e4; vertical-align: top;">
                          <p style="margin: 0 0 16px; font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 2px; color: #78716c;">Last Year</p>
                          <table role="presentation" cellpadding="0" cellspacing="0" width="100%">
                            {ly_rows}
                          </table>
                        </td>
                        <td width="50%" style="padding: 20px; background-color: #ffffff; vertical-align: top;">
                          <p style="margin: 0 0 16px; font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 2px; color: {primary_color};">This Year</p>
                          <table role="presentation" cellpadding="0" cellspacing="0" width="100%">
                            {ty_rows}
                          </table>
                        </td>
                      </tr>
                    </table>
                  </td>
                </tr>
              </table>'''


# ---------------------------------------------------------------------------
# Phase 2: Photo Card Builders
# ---------------------------------------------------------------------------

def _listing_price_str(listing: Dict) -> str:
    """Format a listing's price for display."""
    price = listing.get("list_price") or listing.get("close_price")
    if not price:
        return "Price N/A"
    return _format_price_clean(price)


def _build_photo_card_2x2(listing: Dict, primary_color: str) -> str:
    """Market Narrative 2x2 card: 160px photo, 18px serif price. Ref: V0 market-narrative.tsx"""
    photo = listing.get("hero_photo_url") or ""
    addr = listing.get("street_address") or "Address N/A"
    city = listing.get("city") or ""
    beds = listing.get("bedrooms")
    baths = listing.get("bathrooms")
    price_str = _listing_price_str(listing)
    photo_html = f'<img src="{photo}" alt="{addr}" width="260" height="160" style="display: block; width: 100%; height: 160px; object-fit: cover;">' if photo else '<div style="width: 100%; height: 160px; background: #f5f5f4;"></div>'
    badges = ""
    if beds:
        badges += f'<span style="display: inline-block; padding: 2px 8px; background-color: {primary_color}0D; border-radius: 4px; font-size: 10px; font-weight: 500; color: {primary_color}; margin-right: 4px;">{beds} Bed</span>'
    if baths:
        badges += f'<span style="display: inline-block; padding: 2px 8px; background-color: {primary_color}0D; border-radius: 4px; font-size: 10px; font-weight: 500; color: {primary_color};">{baths} Bath</span>'
    return f'''<table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="border: 1px solid #e7e5e4; border-radius: 8px; overflow: hidden; background-color: #ffffff;">
                        <tr><td>{photo_html}</td></tr>
                        <tr><td style="padding: 12px;">
                          <p style="margin: 0 0 4px; font-family: Georgia, 'Times New Roman', serif; font-size: 18px; font-weight: 700; color: {primary_color};">{price_str}</p>
                          <p style="margin: 0 0 2px; font-size: 13px; font-weight: 600; color: #1c1917;">{addr}</p>
                          <p style="margin: 0 0 8px; font-size: 11px; color: #78716c;">{city}</p>
                          {f'<p style="margin: 0;">{badges}</p>' if badges else ''}
                        </td></tr>
                      </table>'''


def _build_gallery_card_large(listing: Dict, primary_color: str) -> str:
    """Gallery 2x2 card: 180px photo, 20px serif price. Ref: V0 gallery-2x2.tsx"""
    photo = listing.get("hero_photo_url") or ""
    addr = listing.get("street_address") or "Address N/A"
    city = listing.get("city") or ""
    zip_code = listing.get("zip_code") or ""
    beds = listing.get("bedrooms")
    baths = listing.get("bathrooms")
    sqft = listing.get("sqft")
    price_str = _listing_price_str(listing)
    location = f"{city}, {zip_code}" if zip_code else city
    photo_html = f'<img src="{photo}" alt="{addr}" width="260" height="180" style="display: block; width: 100%; height: 180px; object-fit: cover;">' if photo else '<div style="width: 100%; height: 180px; background: #f5f5f4;"></div>'
    details = []
    if beds:
        details.append(f"{beds} Bed")
    if baths:
        details.append(f"{baths} Bath")
    if sqft:
        details.append(f"{sqft:,} SF")
    details_str = " &bull; ".join(details)
    return f'''<table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="border: 1px solid #e7e5e4; border-radius: 8px; overflow: hidden; background-color: #ffffff;">
                        <tr><td>{photo_html}</td></tr>
                        <tr><td style="padding: 16px;">
                          <p style="margin: 0 0 4px; font-family: Georgia, 'Times New Roman', serif; font-size: 20px; font-weight: 700; color: {primary_color};">{price_str}</p>
                          <p style="margin: 0 0 2px; font-size: 14px; font-weight: 600; color: #1c1917;">{addr}</p>
                          <p style="margin: 0 0 8px; font-size: 12px; color: #78716c;">{location}</p>
                          <p style="margin: 0; font-size: 12px; color: #57534e;">{details_str}</p>
                        </td></tr>
                      </table>'''


def _build_gallery_card_compact(listing: Dict, primary_color: str) -> str:
    """Gallery 3x2 card: 110px photo, 15px serif price. Ref: V0 gallery-3x2.tsx"""
    photo = listing.get("hero_photo_url") or ""
    addr = listing.get("street_address") or "Address N/A"
    beds = listing.get("bedrooms")
    baths = listing.get("bathrooms")
    price_str = _listing_price_str(listing)
    photo_html = f'<img src="{photo}" alt="{addr}" width="180" height="110" style="display: block; width: 100%; height: 110px; object-fit: cover;">' if photo else '<div style="width: 100%; height: 110px; background: #f5f5f4;"></div>'
    specs = f'{beds}bd / {baths}ba' if beds and baths else ""
    return f'''<table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="border: 1px solid #e7e5e4; border-radius: 8px; overflow: hidden; background-color: #ffffff;">
                        <tr><td>{photo_html}</td></tr>
                        <tr><td style="padding: 10px;">
                          <p style="margin: 0 0 2px; font-family: Georgia, 'Times New Roman', serif; font-size: 15px; font-weight: 700; color: {primary_color};">{price_str}</p>
                          <p style="margin: 0 0 2px; font-size: 11px; font-weight: 500; color: #1c1917;">{addr}</p>
                          <p style="margin: 0; font-size: 10px; color: #78716c;">{specs}</p>
                        </td></tr>
                      </table>'''


def _build_stacked_property_card(listing: Dict, primary_color: str, accent_color: str) -> str:
    """Full-width card: 240px hero photo, 22px price, description. Ref: V0 single-stacked.tsx"""
    photo = listing.get("hero_photo_url") or ""
    addr = listing.get("street_address") or "Address N/A"
    city = listing.get("city") or ""
    zip_code = listing.get("zip_code") or ""
    beds = listing.get("bedrooms")
    baths = listing.get("bathrooms")
    sqft = listing.get("sqft")
    price_str = _listing_price_str(listing)
    location = f"{city}, {zip_code}" if zip_code else city
    photo_html = f'<img src="{photo}" alt="{addr}" width="520" height="240" style="display: block; width: 100%; height: 240px; object-fit: cover;">' if photo else '<div style="width: 100%; height: 240px; background: #f5f5f4;"></div>'
    badge_items = []
    if beds:
        badge_items.append(f"{beds} Bed")
    if baths:
        badge_items.append(f"{baths} Bath")
    if sqft:
        badge_items.append(f"{sqft:,} SF")
    badges = ""
    for b in badge_items:
        badges += f'<td style="padding-right: 6px;"><span style="display: inline-block; padding: 4px 12px; background-color: {primary_color}0D; border-radius: 6px; font-size: 11px; font-weight: 500; color: {primary_color};">{b}</span></td>'
    return f'''
              <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="border: 1px solid #e7e5e4; border-radius: 12px; overflow: hidden; background-color: #ffffff;">
                <tr><td>{photo_html}</td></tr>
                <tr><td style="padding: 20px;">
                  <p style="margin: 0 0 4px; font-family: Georgia, 'Times New Roman', serif; font-size: 22px; font-weight: 700; color: {primary_color};">{price_str}</p>
                  <p style="margin: 0 0 2px; font-size: 15px; font-weight: 600; color: #1c1917;">{addr}</p>
                  <p style="margin: 0 0 16px; font-size: 12px; color: #78716c;">{location}</p>
                  <table role="presentation" cellpadding="0" cellspacing="0"><tr>{badges}</tr></table>
                </td></tr>
              </table>'''


def _build_photo_card_with_badge(listing: Dict, primary_color: str, accent_color: str, badge_text: str = "Sold") -> str:
    """Card with badge overlay (SOLD/NEW). Ref: V0 closed-sales-table.tsx"""
    photo = listing.get("hero_photo_url") or ""
    addr = listing.get("street_address") or "Address N/A"
    beds = listing.get("bedrooms")
    baths = listing.get("bathrooms")
    price_str = _listing_price_str(listing)
    photo_html = f'<img src="{photo}" alt="{addr}" width="260" height="130" style="display: block; width: 100%; height: 130px; object-fit: cover;">' if photo else '<div style="width: 100%; height: 130px; background: #f5f5f4;"></div>'
    specs = f'{beds}bd / {baths}ba' if beds and baths else ""
    badge_bg = primary_color if badge_text == "Sold" else accent_color
    return f'''<table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="border: 1px solid #e7e5e4; border-radius: 8px; overflow: hidden; background-color: #ffffff;">
                        <tr><td>{photo_html}</td></tr>
                        <tr><td style="padding: 12px;">
                          <table role="presentation" cellpadding="0" cellspacing="0" width="100%"><tr>
                            <td style="vertical-align: middle;">
                              <p style="margin: 0 0 2px; font-family: Georgia, 'Times New Roman', serif; font-size: 16px; font-weight: 700; color: {primary_color};">{price_str}</p>
                            </td>
                            <td align="right" style="vertical-align: top;">
                              <span style="display: inline-block; padding: 2px 8px; background-color: {badge_bg}; color: #ffffff; font-size: 9px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; border-radius: 4px;">{badge_text}</span>
                            </td>
                          </tr></table>
                          <p style="margin: 4px 0 2px; font-size: 12px; font-weight: 500; color: #1c1917;">{addr}</p>
                          <p style="margin: 0; font-size: 10px; color: #78716c;">{specs}</p>
                        </td></tr>
                      </table>'''


def _build_property_row(listing: Dict, primary_color: str, is_last: bool = False) -> str:
    """Photo-left (160x120), details-right row. Ref: V0 large-list.tsx"""
    photo = listing.get("hero_photo_url") or ""
    addr = listing.get("street_address") or "Address N/A"
    city = listing.get("city") or ""
    zip_code = listing.get("zip_code") or ""
    beds = listing.get("bedrooms")
    baths = listing.get("bathrooms")
    sqft = listing.get("sqft")
    price_str = _listing_price_str(listing)
    location = f"{city}, {zip_code}" if zip_code else city
    photo_html = f'<img src="{photo}" alt="{addr}" width="160" height="120" style="display: block; width: 160px; height: 120px; object-fit: cover;">' if photo else '<div style="width: 160px; height: 120px; background: #f5f5f4;"></div>'
    details = []
    if beds:
        details.append(f"{beds} Bed")
    if baths:
        details.append(f"{baths} Bath")
    if sqft:
        details.append(f"{sqft:,} SF")
    details_str = " &bull; ".join(details)
    border = "" if is_last else "border-bottom: 1px solid #f5f5f4;"
    return f'''
                      <tr>
                        <td style="{border}">
                          <table role="presentation" cellpadding="0" cellspacing="0" width="100%">
                            <tr>
                              <td width="160" style="vertical-align: top;">
                                {photo_html}
                              </td>
                              <td style="vertical-align: middle; padding: 16px;">
                                <p style="margin: 0 0 4px; font-family: Georgia, 'Times New Roman', serif; font-size: 18px; font-weight: 700; color: {primary_color};">{price_str}</p>
                                <p style="margin: 0 0 2px; font-size: 14px; font-weight: 600; color: #1c1917;">{addr}</p>
                                <p style="margin: 0 0 8px; font-size: 12px; color: #78716c;">{location}</p>
                                <p style="margin: 0; font-size: 11px; color: #57534e;">{details_str}</p>
                              </td>
                            </tr>
                          </table>
                        </td>
                      </tr>'''


def _build_sales_table(listings: List[Dict], primary_color: str) -> str:
    """Branded data table for Closed Sales / Inventory. Ref: V0 closed-sales-table.tsx"""
    if not listings:
        return ""
    rows = ""
    for i, listing in enumerate(listings):
        addr = listing.get("street_address") or "N/A"
        beds = listing.get("bedrooms") or ""
        baths = listing.get("bathrooms") or ""
        price = listing.get("close_price") or listing.get("list_price")
        dom = listing.get("days_on_market") or ""
        price_str = _format_price_clean(price) if price else "N/A"
        specs = f"{beds}/{baths}" if beds and baths else ""
        bg = "#ffffff" if i % 2 == 0 else "#fafaf9"
        rows += f'''
                        <tr style="background-color: {bg};">
                          <td style="padding: 10px 12px; font-size: 13px; font-weight: 500; color: #1c1917;">{addr}</td>
                          <td align="center" style="padding: 10px 8px; font-size: 13px; color: #57534e;">{specs}</td>
                          <td align="right" style="padding: 10px 12px; font-family: Georgia, 'Times New Roman', serif; font-size: 13px; font-weight: 600; color: {primary_color};">{price_str}</td>
                          <td align="center" style="padding: 10px 8px; font-size: 13px; color: #57534e;">{dom}</td>
                        </tr>'''
    return f'''
              <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="margin-bottom: 32px; border: 1px solid #e7e5e4; border-radius: 12px; overflow: hidden;">
                <tr style="background-color: {primary_color};">
                  <td style="padding: 10px 12px; font-size: 10px; font-weight: 700; color: #ffffff; text-transform: uppercase; letter-spacing: 0.5px;">Address</td>
                  <td align="center" style="padding: 10px 8px; font-size: 10px; font-weight: 700; color: #ffffff; text-transform: uppercase;">Bd/Ba</td>
                  <td align="right" style="padding: 10px 12px; font-size: 10px; font-weight: 700; color: #ffffff; text-transform: uppercase;">Price</td>
                  <td align="center" style="padding: 10px 8px; font-size: 10px; font-weight: 700; color: #ffffff; text-transform: uppercase;">DOM</td>
                </tr>
                {rows}
              </table>'''


# ---------------------------------------------------------------------------
# Phase 3: Layout Body Builders
# Each returns the HTML between the content wrapper open and agent footer.
# ---------------------------------------------------------------------------

def _build_market_narrative_body(
    insight_text: str, hero_value: str, hero_label: str,
    stats: List[Tuple[str, str]], quick_take: str,
    pdf_url: str, primary_color: str, accent_color: str,
    filter_description: str = None,
    listings: List[Dict] = None,
) -> str:
    """Market Snapshot / New Listings / Price Bands layout.
    Ref: V0 market-narrative.tsx"""
    body = _build_filter_blurb(filter_description, primary_color)
    body += _build_ai_narrative(insight_text)
    body += _build_hero_stat(hero_value, hero_label, primary_color)
    if listings and len(listings) >= 2:
        show = listings[:4]
        body += _build_gallery_count(len(show), "Notable Sales", primary_color)
        body += _build_2x2_photo_grid(show, primary_color)
    body += _build_stacked_stats(stats)
    body += _build_quick_take(quick_take, accent_color)
    body += _build_cta(pdf_url, primary_color)
    return body


def _build_2x2_photo_grid(listings: List[Dict], primary_color: str) -> str:
    """2x2 grid of photo cards for Market Narrative. Ref: V0 market-narrative.tsx"""
    cards = [_build_photo_card_2x2(l, primary_color) for l in listings[:4]]
    while len(cards) < 4:
        cards.append("")
    rows = ""
    for r in range(0, len(cards), 2):
        c1 = cards[r] if r < len(cards) else ""
        c2 = cards[r + 1] if r + 1 < len(cards) else ""
        rows += f'''
                <tr>
                  <td width="50%" style="padding: 0 4px 8px 0; vertical-align: top;">{c1}</td>
                  <td width="50%" style="padding: 0 0 8px 4px; vertical-align: top;">{c2}</td>
                </tr>'''
    return f'''
              <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="margin-bottom: 32px;">
                {rows}
              </table>'''


def _build_gallery_2x2_body(
    insight_text: str, listings: List[Dict], quick_take: str,
    pdf_url: str, primary_color: str, accent_color: str,
    gallery_label: str = "Featured Listings", filter_description: str = None,
) -> str:
    """Gallery 2x2 layout: large photo cards. Ref: V0 gallery-2x2.tsx"""
    body = _build_filter_blurb(filter_description, primary_color)
    body += _build_ai_narrative(insight_text)
    body += _build_gallery_count(len(listings), gallery_label, primary_color)
    cards = [_build_gallery_card_large(l, primary_color) for l in listings[:4]]
    rows = ""
    for r in range(0, len(cards), 2):
        c1 = cards[r] if r < len(cards) else ""
        c2 = cards[r + 1] if r + 1 < len(cards) else ""
        rows += f'''
                <tr>
                  <td width="50%" style="padding: 0 4px 8px 0; vertical-align: top;">{c1}</td>
                  <td width="50%" style="padding: 0 0 8px 4px; vertical-align: top;">{c2}</td>
                </tr>'''
    body += f'''
              <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="margin-bottom: 32px;">
                {rows}
              </table>'''
    body += _build_quick_take(quick_take, accent_color)
    body += _build_cta(pdf_url, primary_color, "View All Listings")
    return body


def _build_gallery_3x2_body(
    insight_text: str, listings: List[Dict], quick_take: str,
    pdf_url: str, primary_color: str, accent_color: str,
    gallery_label: str = "New Listings", filter_description: str = None,
) -> str:
    """Gallery 3x2 layout: compact photo cards. Ref: V0 gallery-3x2.tsx"""
    body = _build_filter_blurb(filter_description, primary_color)
    body += _build_ai_narrative(insight_text)
    body += _build_gallery_count(len(listings), gallery_label, primary_color)
    cards = [_build_gallery_card_compact(l, primary_color) for l in listings[:9]]
    rows = ""
    for r in range(0, len(cards), 3):
        cells = ""
        for c in range(3):
            idx = r + c
            pad = "padding: 0 3px 6px 0;" if c == 0 else ("padding: 0 0 6px 3px;" if c == 2 else "padding: 0 3px 6px 3px;")
            card = cards[idx] if idx < len(cards) else ""
            cells += f'<td width="33%" style="{pad} vertical-align: top;">{card}</td>'
        rows += f'<tr>{cells}</tr>'
    body += f'''
              <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="margin-bottom: 32px;">
                {rows}
              </table>'''
    body += _build_quick_take(quick_take, accent_color)
    body += _build_cta(pdf_url, primary_color, "View All Listings")
    return body


def _build_single_stacked_body(
    insight_text: str, listings: List[Dict],
    pdf_url: str, primary_color: str, accent_color: str,
    filter_description: str = None,
) -> str:
    """Single stacked full-width cards with branded dividers. Ref: V0 single-stacked.tsx"""
    body = _build_filter_blurb(filter_description, primary_color)
    body += _build_ai_narrative(insight_text)
    for i, listing in enumerate(listings[:5]):
        body += _build_stacked_property_card(listing, primary_color, accent_color)
        if i < len(listings) - 1:
            body += _build_branded_divider(primary_color, accent_color)
    body += _build_cta(pdf_url, primary_color, "Schedule a Showing")
    return body


def _build_large_list_body(
    insight_text: str, listings: List[Dict], quick_take: str,
    pdf_url: str, primary_color: str, accent_color: str,
    gallery_label: str = "New Listings", filter_description: str = None,
) -> str:
    """Vertical list: photo-left, details-right. Ref: V0 large-list.tsx"""
    body = _build_filter_blurb(filter_description, primary_color)
    body += _build_ai_narrative(insight_text)
    body += _build_gallery_count(len(listings), gallery_label, primary_color)
    rows = ""
    for i, listing in enumerate(listings):
        rows += _build_property_row(listing, primary_color, is_last=(i == len(listings) - 1))
    body += f'''
              <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="margin-bottom: 32px; border: 1px solid #e7e5e4; border-radius: 12px; overflow: hidden;">
                {rows}
              </table>'''
    body += _build_quick_take(quick_take, accent_color)
    body += _build_cta(pdf_url, primary_color)
    return body


def _build_closed_sales_body(
    insight_text: str, hero_value: str, hero_label: str,
    listings: List[Dict], stats: List[Tuple[str, str]], quick_take: str,
    pdf_url: str, primary_color: str, accent_color: str,
    filter_description: str = None,
) -> str:
    """Closed Sales / Inventory table layout. Ref: V0 closed-sales-table.tsx"""
    body = _build_filter_blurb(filter_description, primary_color)
    body += _build_ai_narrative(insight_text)
    body += _build_hero_stat(hero_value, hero_label, primary_color)
    if listings and len(listings) >= 2:
        show = listings[:4]
        label = "Notable Sales" if any(l.get("close_price") for l in show) else "Featured Properties"
        body += _build_gallery_count(len(show), label, primary_color)
        cards = [_build_photo_card_with_badge(l, primary_color, accent_color, "Sold" if l.get("close_price") else "Active") for l in show]
        rows = ""
        for r in range(0, len(cards), 2):
            c1 = cards[r] if r < len(cards) else ""
            c2 = cards[r + 1] if r + 1 < len(cards) else ""
            rows += f'''
                <tr>
                  <td width="50%" style="padding: 0 4px 8px 0; vertical-align: top;">{c1}</td>
                  <td width="50%" style="padding: 0 0 8px 4px; vertical-align: top;">{c2}</td>
                </tr>'''
        body += f'''
              <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="margin-bottom: 32px;">
                {rows}
              </table>'''
    body += _build_sales_table(listings or [], primary_color)
    body += _build_stacked_stats(stats)
    body += _build_quick_take(quick_take, accent_color)
    body += _build_cta(pdf_url, primary_color, "Get Your Home's Value")
    return body


def _build_analytics_body(
    insight_text: str, hero_value: str, hero_label: str,
    trend_stats: List[Tuple[str, str, str, bool]],
    quick_take: str, pdf_url: str, primary_color: str, accent_color: str,
    filter_description: str = None,
) -> str:
    """Analytics dashboard layout. Ref: V0 market-analytics.tsx"""
    body = _build_filter_blurb(filter_description, primary_color)
    body += _build_ai_narrative(insight_text)
    body += _build_hero_stat(hero_value, hero_label, primary_color)
    body += _build_trend_stats(trend_stats, primary_color)
    body += _build_quick_take(quick_take, accent_color)
    body += _build_cta(pdf_url, primary_color, "Get Your Free Home Valuation")
    return body


# ---------------------------------------------------------------------------
# Phase 4: Layout Routing
# ---------------------------------------------------------------------------

def _select_gallery_layout(listing_count: int) -> str:
    """Pick gallery layout name based on listing count. Ref: V8 adaptive layouts."""
    if listing_count <= 3:
        return "single_stacked"
    elif listing_count in (4,):
        return "gallery_2x2"
    elif listing_count in (6, 9):
        return "gallery_3x2"
    else:
        return "large_list"


LAYOUT_MAP = {
    "market_snapshot": "market_narrative",
    "new_listings": "market_narrative",
    "price_bands": "market_narrative",
    "open_houses": "market_narrative",
    "closed": "closed_sales",
    "inventory": "closed_sales",
    "new_listings_gallery": "gallery",
    "featured_listings": "gallery",
}


def _format_decimal(value: Optional[float], decimals: int = 1) -> str:
    """Format decimal for display."""
    if value is None:
        return "N/A"
    return f"{value:.{decimals}f}"


def _get_metrics_for_report_type(
    report_type: str, 
    metrics: Dict,
    total_shown: int = 0
) -> Tuple[Tuple[str, str], Tuple[str, str], Tuple[str, str]]:
    """
    Get the 3 main metrics to display based on report type.
    Returns: ((label1, value1), (label2, value2), (label3, value3))
    """
    # Extract common metrics with defaults
    total_active = metrics.get("total_active", 0)
    total_pending = metrics.get("total_pending", 0)
    total_closed = metrics.get("total_closed", 0)
    total_listings = metrics.get("total_listings", total_active)
    new_this_month = metrics.get("new_this_month", 0)
    median_list_price = metrics.get("median_list_price")
    median_close_price = metrics.get("median_close_price")
    avg_dom = metrics.get("avg_dom")
    median_dom = metrics.get("median_dom", avg_dom)
    
    # Format DOM
    dom_display = f"{avg_dom:.0f}" if avg_dom else "N/A"
    median_dom_display = f"{median_dom:.0f}" if median_dom else dom_display
    
    if report_type == "market_snapshot":
        return (
            ("Active Listings", _format_number(total_active)),
            ("Median Price", _format_price_clean(median_close_price or median_list_price)),
            ("Avg DOM", f"{dom_display} days" if dom_display != "N/A" else "N/A"),
        )
    
    elif report_type == "new_listings":
        return (
            ("New Listings", _format_number(total_active)),
            ("Median Price", _format_price_clean(median_list_price)),
            ("Avg DOM", f"{dom_display} days" if dom_display != "N/A" else "N/A"),
        )
    
    elif report_type == "closed":
        return (
            ("Homes Sold", _format_number(total_closed)),
            ("Median Price", _format_price_clean(median_close_price)),
            ("Avg Days to Sell", f"{dom_display}" if dom_display != "N/A" else "N/A"),
        )
    
    elif report_type == "new_listings_gallery":
        # V14: Show "Showing X of Y" when curated
        if total_shown and total_shown < total_listings:
            listing_display = f"{total_shown} of {_format_number(total_listings)}"
        else:
            listing_display = _format_number(total_listings)
        return (
            ("New Listings", listing_display),
            ("Median Price", _format_price_clean(median_list_price)),
            ("Starting At", _format_price_clean(metrics.get("min_price"))),
        )
    
    elif report_type == "featured_listings":
        # V14: Show "Showing X of Y" when curated
        if total_shown and total_shown < total_listings:
            listing_display = f"{total_shown} of {_format_number(total_listings)}"
        else:
            listing_display = _format_number(total_listings)
        return (
            ("Featured Homes", listing_display),
            ("Highest Price", _format_price_clean(metrics.get("max_price"))),
            ("Avg Sq Ft", _format_number(metrics.get("avg_sqft"))),
        )
    
    elif report_type == "inventory":
        return (
            ("Active Listings", _format_number(total_active)),
            ("New This Month", _format_number(new_this_month)),
            ("Median DOM", f"{median_dom_display} days" if median_dom_display != "N/A" else "N/A"),
        )
    
    elif report_type == "price_bands":
        band_count = len(metrics.get("bands", [])) or 3
        return (
            ("Total Listings", _format_number(total_active or total_listings)),
            ("Median Price", _format_price_clean(median_list_price)),
            ("Price Tiers", str(band_count)),
        )
    
    elif report_type == "open_houses":
        return (
            ("Open Houses", _format_number(total_active)),
            ("Saturday", _format_number(metrics.get("saturday_count", 0))),
            ("Sunday", _format_number(metrics.get("sunday_count", 0))),
        )
    
    else:
        # Generic fallback
        return (
            ("Properties", _format_number(total_active)),
            ("Median Price", _format_price_clean(median_list_price)),
            ("Avg DOM", f"{dom_display} days" if dom_display != "N/A" else "N/A"),
        )


def _get_extra_stats(report_type: str, metrics: Dict) -> Optional[Tuple[Tuple[str, str], Tuple[str, str]]]:
    """
    Get extra stats for reports that support them.
    Returns: ((label1, value1), (label2, value2)) or None
    """
    if report_type == "market_snapshot":
        moi = metrics.get("months_of_inventory")
        ctl = metrics.get("sale_to_list_ratio") or metrics.get("close_to_list_ratio")
        moi_display = _format_decimal(moi) if moi else "N/A"
        ctl_display = _format_percent(ctl) if ctl else "N/A"
        return (
            (moi_display, "Months of Inventory"),
            (ctl_display, "Close-to-List Ratio"),
        )
    
    elif report_type == "closed":
        ctl = metrics.get("sale_to_list_ratio") or metrics.get("close_to_list_ratio")
        volume = metrics.get("total_volume")
        ctl_display = _format_percent(ctl) if ctl else "N/A"
        volume_display = _format_price_clean(volume) if volume else "N/A"
        return (
            (ctl_display, "Close-to-List Ratio"),
            (volume_display, "Total Volume"),
        )
    
    return None


def _get_price_bands(metrics: Dict) -> Optional[List[Dict]]:
    """
    Get price bands for price_bands report.
    Returns list of {name, range, count, color} or None
    
    V3.1: Uses monochromatic PRIMARY color for all bands for visual cohesion.
    """
    bands = metrics.get("bands", [])
    if not bands:
        # Try to construct from individual fields
        entry_count = metrics.get("entry_count")
        if entry_count is not None:
            return [
                {
                    "name": "Entry Level",
                    "range": metrics.get("entry_range", "$0 - Median"),
                    "count": entry_count,
                    "color": "PRIMARY",  # Monochromatic
                },
                {
                    "name": "Move-Up",
                    "range": metrics.get("moveup_range", "Median - 75th"),
                    "count": metrics.get("moveup_count", 0),
                    "color": "PRIMARY",  # Monochromatic
                },
                {
                    "name": "Luxury",
                    "range": metrics.get("luxury_range", "75th+"),
                    "count": metrics.get("luxury_count", 0),
                    "color": "PRIMARY",  # Monochromatic
                },
            ]
    
    # Map bands from metrics - all use PRIMARY for monochromatic design
    if bands:
        return [
            {
                "name": b.get("name", f"Band {i+1}"),
                "range": b.get("range", ""),
                "count": b.get("count", 0),
                "color": "PRIMARY",  # Monochromatic
            }
            for i, b in enumerate(bands)
        ]
    
    return None


def _get_property_type_breakdown(metrics: Dict) -> Optional[List[Dict]]:
    """
    Get property type breakdown for Market Snapshot.
    Returns list of {name, count, icon} or None
    
    V4.1: Updated to modern, minimal icons
    """
    # Try to get from metrics
    property_types = metrics.get("property_types", {})
    
    # Also check for individual fields
    sfr_count = property_types.get("sfr") or metrics.get("sfr_count", 0)
    condo_count = property_types.get("condo") or metrics.get("condo_count", 0)
    townhome_count = property_types.get("townhome") or metrics.get("townhome_count", 0)
    other_count = property_types.get("other") or metrics.get("other_type_count", 0)
    
    # If we have any counts, return the breakdown
    # V4.1: Modern icons - ◼ squares with labels
    if sfr_count or condo_count or townhome_count or other_count:
        result = []
        if sfr_count:
            result.append({"name": "Single Family", "count": sfr_count, "icon": "▪"})
        if condo_count:
            result.append({"name": "Condos", "count": condo_count, "icon": "▪"})
        if townhome_count:
            result.append({"name": "Townhomes", "count": townhome_count, "icon": "▪"})
        if other_count:
            result.append({"name": "Other", "count": other_count, "icon": "▪"})
        return result if result else None
    
    return None


def _get_price_tier_breakdown(metrics: Dict) -> Optional[List[Dict]]:
    """
    Get price tier breakdown for Market Snapshot.
    Returns list of {name, count, range, color} or None
    """
    # Try to get from metrics
    price_tiers = metrics.get("price_tiers", {})
    
    # Also check for individual fields
    entry_count = price_tiers.get("entry") or metrics.get("entry_tier_count", 0)
    moveup_count = price_tiers.get("moveup") or metrics.get("moveup_tier_count", 0)
    luxury_count = price_tiers.get("luxury") or metrics.get("luxury_tier_count", 0)
    
    # Get ranges if available
    entry_range = price_tiers.get("entry_range") or metrics.get("entry_tier_range", "Under $500K")
    moveup_range = price_tiers.get("moveup_range") or metrics.get("moveup_tier_range", "$500K - $1M")
    luxury_range = price_tiers.get("luxury_range") or metrics.get("luxury_tier_range", "$1M+")
    
    # If we have any counts, return the breakdown
    # Using PRIMARY for all tiers - opacity variations applied in template
    if entry_count or moveup_count or luxury_count:
        return [
            {"name": "Entry Level", "count": entry_count, "range": entry_range, "color": "PRIMARY", "opacity": "40"},
            {"name": "Move-Up", "count": moveup_count, "range": moveup_range, "color": "PRIMARY", "opacity": "70"},
            {"name": "Luxury", "count": luxury_count, "range": luxury_range, "color": "PRIMARY", "opacity": "100"},
        ]
    
    return None


# ============================================================================
# V4 FUNCTIONS: PDF-aligned email structure for Market Snapshot
# ============================================================================

def _get_hero_4_metrics(report_type: str, metrics: Dict) -> Tuple[
    Tuple[str, str], Tuple[str, str], Tuple[str, str], Tuple[str, str]
]:
    """
    V4: Get 4 hero metrics that match the PDF report header.
    Returns: ((label1, value1), (label2, value2), (label3, value3), (label4, value4))
    
    Each report type has its own relevant metrics matching the PDF ribbon.
    """
    # Extract common metrics
    median_close_price = metrics.get("median_close_price")
    median_list_price = metrics.get("median_list_price")
    total_active = metrics.get("total_active", 0)
    total_closed = metrics.get("total_closed", 0)
    avg_dom = metrics.get("avg_dom")
    moi = metrics.get("months_of_inventory")
    avg_ppsf = metrics.get("avg_ppsf")
    ctl = metrics.get("sale_to_list_ratio") or metrics.get("close_to_list_ratio")
    new_this_month = metrics.get("new_this_month", total_active)
    
    if report_type == "market_snapshot":
        # Matches PDF: Median Sale Price, Closed Sales, Avg DOM, MOI
        return (
            ("Median Sale Price", _format_price_clean(median_close_price or median_list_price)),
            ("Closed Sales", _format_number(total_closed)),
            ("Avg Days on Market", f"{avg_dom:.0f}" if avg_dom else "N/A"),
            ("Months of Inventory", f"{moi:.1f}" if moi else "N/A"),
        )
    
    elif report_type == "new_listings":
        # Matches PDF: Total Listings, Median List Price, Avg DOM, Avg $/SqFt
        return (
            ("New Listings", _format_number(total_active)),
            ("Median Price", _format_price_clean(median_list_price)),
            ("Avg DOM", f"{avg_dom:.0f}" if avg_dom else "N/A"),
            ("Avg $/SqFt", _format_price_clean(avg_ppsf) if avg_ppsf else "N/A"),
        )
    
    elif report_type == "inventory":
        # Matches PDF: Active Listings, New This Month, Median DOM, MOI
        return (
            ("Active Listings", _format_number(total_active)),
            ("New This Month", _format_number(new_this_month)),
            ("Median DOM", f"{avg_dom:.0f}" if avg_dom else "N/A"),
            ("Months of Inventory", f"{moi:.1f}" if moi else "N/A"),
        )
    
    elif report_type == "closed":
        # Matches PDF: Total Closed, Median Close Price, Avg DOM, Close-to-List
        return (
            ("Total Closed", _format_number(total_closed)),
            ("Median Price", _format_price_clean(median_close_price)),
            ("Avg DOM", f"{avg_dom:.0f}" if avg_dom else "N/A"),
            ("Close-to-List", f"{ctl:.1f}%" if ctl else "N/A"),
        )
    
    elif report_type == "price_bands":
        # Matches PDF: Total Listings, Median Price, Avg DOM, Price Range
        min_price = metrics.get("min_price")
        max_price = metrics.get("max_price")
        price_range = f"{_format_price_clean(min_price)}-{_format_price_clean(max_price)}" if min_price and max_price else "N/A"
        return (
            ("Total Listings", _format_number(total_active)),
            ("Median Price", _format_price_clean(median_list_price)),
            ("Avg DOM", f"{avg_dom:.0f}" if avg_dom else "N/A"),
            ("Price Range", price_range),
        )
    
    else:
        # Generic fallback
        return (
            ("Properties", _format_number(total_active)),
            ("Median Price", _format_price_clean(median_list_price or median_close_price)),
            ("Avg DOM", f"{avg_dom:.0f}" if avg_dom else "N/A"),
            ("MOI", f"{moi:.1f}" if moi else "N/A"),
        )


def _get_core_indicators(metrics: Dict) -> Tuple[
    Tuple[str, str], Tuple[str, str], Tuple[str, str]
]:
    """
    V4: Get 3 core indicator metrics that match the PDF report.
    Returns: ((label1, value1), (label2, value2), (label3, value3))
    
    PDF Core Indicators:
    1. New Listings (or Active Listings if new not available)
    2. Pending Sales
    3. Sale-to-List Ratio
    """
    # Extract metrics
    new_listings = metrics.get("new_listings_7d") or metrics.get("total_active", 0)
    total_pending = metrics.get("total_pending", 0)
    ctl = metrics.get("sale_to_list_ratio") or metrics.get("close_to_list_ratio")
    
    # Format values
    new_val = _format_number(new_listings)
    pending_val = _format_number(total_pending)
    ctl_val = f"{ctl:.1f}%" if ctl else "N/A"
    
    return (
        ("New Listings", new_val),
        ("Pending Sales", pending_val),
        ("Sale-to-List Ratio", ctl_val),
    )


def _get_insight_paragraph(
    report_type: str, 
    area: str, 
    metrics: Dict, 
    lookback_days: int,
    filter_description: str = None,
    sender_type: str = "REGULAR",
    total_found: int = 0,
    total_shown: int = 0,
    audience_name: str = None,
) -> str:
    """
    V14: Generate insight paragraph for reports with sender/audience awareness.
    
    First tries AI-generated insight via OpenAI (with full context),
    falls back to template-based text if AI is disabled or fails.
    """
    # V14: Try AI-generated insight first with full context
    try:
        from ..ai_insights import generate_insight, AI_INSIGHTS_ENABLED
        print(f"[INSIGHT] Generating for {report_type} in {area}, sender={sender_type}, AI_ENABLED={AI_INSIGHTS_ENABLED}")
        ai_insight = generate_insight(
            report_type=report_type,
            area=area,
            metrics=metrics,
            lookback_days=lookback_days,
            filter_description=filter_description,
            sender_type=sender_type,
            total_found=total_found,
            total_shown=total_shown,
            audience_name=audience_name,
        )
        if ai_insight:
            print(f"[INSIGHT] AI SUCCESS: {ai_insight[:80]}...")
            return ai_insight
        else:
            print(f"[INSIGHT] AI returned None, using fallback")
    except ImportError as e:
        print(f"[INSIGHT] Import error: {e}")
    except Exception as e:
        print(f"[INSIGHT] Exception: {e}")
    
    # Fallback: Template-based text (V13: More exciting and personable)
    print(f"[INSIGHT] Using FALLBACK template for {report_type}")
    # Extract key metrics for narrative
    total_active = metrics.get("total_active", 0)
    total_closed = metrics.get("total_closed", 0)
    median_price = metrics.get("median_close_price") or metrics.get("median_list_price")
    avg_dom = metrics.get("avg_dom")
    moi = metrics.get("months_of_inventory")
    avg_ppsf = metrics.get("avg_ppsf")
    ctl = metrics.get("sale_to_list_ratio") or metrics.get("close_to_list_ratio")
    
    # Build insight text based on report type
    price_str = _format_price_clean(median_price) if median_price else "varying prices"
    dom_str = f"{avg_dom:.0f} days" if avg_dom else "typical time"
    
    if report_type == "market_snapshot":
        # V13: Exciting market update language
        if moi and moi < 3:
            return (
                f"Great news for sellers in {area}—the market is moving fast. "
                f"With only {moi:.1f} months of inventory and {total_closed} homes sold at a median of {price_str}, "
                f"buyers are competing for well-priced properties."
            )
        elif moi and moi > 6:
            return (
                f"Buyers have excellent options in {area} right now. "
                f"With {moi:.1f} months of inventory and homes averaging {dom_str} on market, "
                f"there's room to find the perfect fit without rushing."
            )
        else:
            return (
                f"Healthy activity in {area} this month—{total_closed} families found their new home "
                f"at a median price of {price_str}. With homes averaging {dom_str} on market, "
                f"there's time to explore without missing out."
            )
    
    elif report_type == "new_listings":
        return (
            f"Fresh opportunities in {area}—{total_active} new properties just hit the market. "
            f"With a median asking price of {price_str}, there's something for every buyer. "
            f"These won't last long."
        )
    
    elif report_type == "inventory":
        if moi and moi < 3:
            return (
                f"Inventory is tight in {area}, so move quickly on properties you love. "
                f"{total_active} active listings at a median of {price_str}—competition is real, but so are the opportunities."
            )
        elif moi and moi > 6:
            return (
                f"You have options in {area}—{total_active} active listings and {moi:.1f} months of inventory "
                f"means time to find exactly what you're looking for at a median of {price_str}."
            )
        else:
            return (
                f"The {area} market is well-balanced right now. "
                f"{total_active} active listings at a median of {price_str} give you solid options without extreme competition."
            )
    
    elif report_type == "closed":
        ctl_str = f"{ctl:.1f}%" if ctl else "competitive rates"
        return (
            f"The {area} market is active—{total_closed} homes sold in the last {lookback_days} days "
            f"at a median of {price_str}. Buyers are paying {ctl_str} of asking, "
            f"showing confidence in property values."
        )
    
    elif report_type == "price_bands":
        return (
            f"Price analysis for {area} over the last {lookback_days} days. "
            f"This report segments the market into price ranges to identify where inventory and buyer activity "
            f"are concentrated. Faster-moving bands indicate stronger demand."
        )
    
    elif report_type == "new_listings_gallery":
        # V13: Gallery-specific insight
        total_listings = metrics.get("total_listings", 0)
        min_price = metrics.get("min_price")
        max_price = metrics.get("max_price")
        min_str = _format_price_clean(min_price) if min_price else "various"
        max_str = _format_price_clean(max_price) if max_price else "price points"
        
        if filter_description:
            return (
                f"Fresh opportunities for {filter_description} buyers in {area}. "
                f"We found {total_listings} new listings in the last {lookback_days} days, "
                f"with prices ranging from {min_str} to {max_str}. These curated properties match your specific criteria."
            )
        else:
            return (
                f"The newest listings hitting the market in {area}. "
                f"{total_listings} properties listed in the last {lookback_days} days at a median of {price_str}. "
                f"Don't miss these fresh opportunities."
            )
    
    elif report_type == "featured_listings":
        # V13: Featured listings insight
        total_listings = metrics.get("total_listings", 0)
        max_price = metrics.get("max_price")
        max_str = _format_price_clean(max_price) if max_price else "premium pricing"
        
        return (
            f"Hand-picked properties showcasing the best of {area}. "
            f"These {total_listings} featured homes represent exceptional value and quality, "
            f"with prices reaching {max_str}."
        )
    
    else:
        return (
            f"Market report for {area} covering the last {lookback_days} days. "
            f"Median price: {price_str}. Average days on market: {dom_str}."
        )


def _get_quick_take(report_type: str, area: str, metrics: Dict) -> str:
    """
    V10: Generate a professional market insight one-liner.
    Clean, data-focused language without emojis.
    """
    total_active = metrics.get("total_active", 0)
    total_closed = metrics.get("total_closed", 0)
    median_price = metrics.get("median_close_price") or metrics.get("median_list_price")
    avg_dom = metrics.get("avg_dom")
    moi = metrics.get("months_of_inventory")
    
    price_str = _format_price_clean(median_price) if median_price else None
    
    if report_type == "market_snapshot":
        if moi and moi < 3:
            return f"Seller's market conditions: {moi:.1f} months of inventory indicates strong demand in {area}."
        elif moi and moi > 6:
            return f"Buyer-favorable conditions: {moi:.1f} months of inventory provides negotiating leverage in {area}."
        elif total_closed and price_str:
            return f"{total_closed} closed transactions at {price_str} median price point in {area}."
        else:
            return f"Current market conditions and key indicators for {area}."
    
    elif report_type in ("new_listings", "new_listings_gallery"):
        if total_active and price_str:
            return f"{total_active} new properties listed in {area} with a median asking price of {price_str}."
        elif total_active:
            return f"{total_active} new listings now available in {area}."
        else:
            return f"Latest available properties in {area}."
    
    elif report_type == "closed":
        if total_closed and price_str:
            return f"{total_closed} properties closed in {area} at a {price_str} median sale price."
        elif total_closed:
            return f"{total_closed} recent closings recorded in {area}."
        else:
            return f"Recent closed transactions in {area}."
    
    elif report_type == "featured_listings":
        return f"Selected properties currently available in {area}."
    
    else:
        return f"Market summary for {area}."


def _get_conversation_starter(report_type: str, area: str, metrics: Dict, listings: Optional[List[Dict]] = None) -> str:
    """
    V5: Generate a ready-to-text conversation starter for agents.
    This is what agents can copy and send to their clients.
    """
    total_active = metrics.get("total_active", 0)
    median_price = metrics.get("median_close_price") or metrics.get("median_list_price")
    price_str = _format_price_clean(median_price) if median_price else None
    
    # Try to get a featured listing for personalization
    featured_address = None
    featured_price = None
    if listings and len(listings) > 0:
        first = listings[0]
        featured_address = first.get("street_address")
        featured_price = _format_price_clean(first.get("list_price")) if first.get("list_price") else None
    
    if report_type in ("new_listings", "new_listings_gallery"):
        if featured_address and featured_price:
            return (
                f"Hey! Just saw a new listing at {featured_address} for {featured_price} - "
                f"thought of you. Want me to send you the details?"
            )
        elif total_active:
            return (
                f"Hey! {total_active} new listings just hit the market in {area}. "
                f"Want me to send you the ones that match what you're looking for?"
            )
        else:
            return (
                f"Hey! Some new listings just came up in {area}. "
                f"Let me know if you'd like to take a look!"
            )
    
    elif report_type == "market_snapshot":
        if price_str:
            return (
                f"Hey! Quick update on the {area} market - "
                f"median prices are at {price_str}. Want to chat about what this means for you?"
            )
        else:
            return (
                f"Hey! Just pulled the latest market data for {area}. "
                f"Let me know if you want to talk strategy!"
            )
    
    elif report_type == "closed":
        return (
            f"Hey! Just looked at recent sales in {area} - "
            f"some interesting comps. Want me to walk you through them?"
        )
    
    elif report_type == "featured_listings":
        if featured_address:
            return (
                f"Hey! I think you'll love this one - {featured_address}. "
                f"Free this weekend to take a look?"
            )
        else:
            return (
                f"Hey! Found some great properties in {area} I think you'll love. "
                f"When can we chat?"
            )
    
    else:
        return (
            f"Hey! Just pulled some fresh market data for {area}. "
            f"Let me know when you have a few minutes to chat!"
        )


def _build_preheader(report_type: str, area: str, metrics: Dict) -> str:
    """Build preheader text for email preview. V10: Professional tone without emojis."""
    config = REPORT_CONFIG.get(report_type, {})
    label = config.get("label", "Report")
    
    # Get a key metric for the preheader
    if report_type == "market_snapshot":
        count = metrics.get("total_active", 0)
        return f"{label} for {area}: {count} active listings, median prices, and market trends"
    elif report_type == "new_listings":
        count = metrics.get("total_active", 0)
        return f"{count} new listings in {area} - prices, photos, and property details"
    elif report_type == "closed":
        count = metrics.get("total_closed", 0)
        return f"{count} closed sales in {area} - sale prices and market activity"
    elif report_type == "price_bands":
        return f"Price analysis for {area} - entry, move-up, and luxury tier breakdown"
    elif report_type == "inventory":
        count = metrics.get("total_active", 0)
        return f"{count} active listings in {area} - current market inventory"
    else:
        return f"Your {label} for {area} is ready"


def schedule_email_html(
    account_name: str,
    report_type: str,
    city: Optional[str],
    zip_codes: Optional[list],
    lookback_days: int,
    metrics: Dict,
    pdf_url: str,
    unsubscribe_url: str,
    brand: Optional[Brand] = None,
    listings: Optional[List[Dict]] = None,
    preset_display_name: Optional[str] = None,
    filter_description: Optional[str] = None,
    sender_type: str = "REGULAR",
    total_found: int = 0,
    total_shown: int = 0,
    audience_name: Optional[str] = None,
) -> str:
    """
    Generate HTML email for a scheduled report notification.
    
    V2: Complete redesign with V0-generated email-safe template.
    V14: Sender-aware AI insights with audience context.
    
    Features:
    - Gradient header with Outlook VML fallback
    - Dark mode support
    - Mobile responsive (metrics stack)
    - Extra stats row for Market Snapshot & Closed Sales
    - Price bands section for Price Bands report
    - Preheader text for email preview
    - Polished agent footer with circular photo
    - V14: AI insights adapt based on sender type and audience
    
    Args:
        account_name: Name of the account (for personalization)
        report_type: Type of report (market_snapshot, new_listings, etc.)
        city: City name (if city-based report)
        zip_codes: List of ZIP codes (if ZIP-based report)
        lookback_days: Number of days covered by the report
        metrics: Dictionary of key metrics to display
        pdf_url: Direct link to the PDF report
        unsubscribe_url: Link to unsubscribe from future emails
        brand: Optional brand configuration (for white-label output)
        sender_type: "REGULAR" (agent) or "INDUSTRY_AFFILIATE" (title company)
        total_found: Total listings in market (for AI context)
        total_shown: How many listings displayed (for AI context)
        audience_name: Preset audience (e.g., "First-Time Buyers")
    
    Returns:
        HTML string for the email body
    """
    # Extract brand values with defaults
    brand = brand or {}
    brand_name = brand.get("display_name") or account_name or "Market Reports"
    logo_url = brand.get("logo_url")
    email_logo_url = brand.get("email_logo_url")  # Separate logo for email headers
    primary_color = brand.get("primary_color") or "#6366f1"  # Indigo
    accent_color = brand.get("accent_color") or "#8b5cf6"    # Purple
    rep_name = brand.get("rep_name")
    rep_title = brand.get("rep_title")
    rep_photo_url = brand.get("rep_photo_url")
    rep_phone = brand.get("rep_phone")
    rep_email = brand.get("rep_email")
    contact_line1 = brand.get("contact_line1") or rep_name
    contact_line2 = brand.get("contact_line2") or rep_title
    website_url = brand.get("website_url")
    
    # Get report config
    config = REPORT_CONFIG.get(report_type, {
        "label": report_type.replace("_", " ").title(),
        "tagline": "Your Market Report",
        "section": "Market Overview",
    })
    # V6: Use preset_display_name if provided (e.g., "First-Time Buyer" instead of "New Listings Gallery")
    report_label = preset_display_name or config.get("label")
    tagline = config.get("tagline")
    section_label = config.get("section")
    has_extra_stats = config.get("has_extra_stats", False)
    has_price_bands = config.get("has_price_bands", False)
    has_property_types = config.get("has_property_types", False)
    has_price_tiers = config.get("has_price_tiers", False)
    
    # V4 features
    has_hero_4 = config.get("has_hero_4", False)
    has_core_indicators = config.get("has_core_indicators", False)
    has_insight = config.get("has_insight", False)
    
    # Format area for display
    if city:
        area_display = city
    elif zip_codes and len(zip_codes) > 0:
        if len(zip_codes) == 1:
            area_display = f"ZIP {zip_codes[0]}"
        elif len(zip_codes) <= 3:
            area_display = f"ZIPs {', '.join(zip_codes)}"
        else:
            area_display = f"{len(zip_codes)} ZIP codes"
    else:
        area_display = "Your Area"
    
    # Date range display
    date_range = f"Last {lookback_days} Days"
    
    # V4: Get 4-metric hero row (for all V4 report types)
    if has_hero_4:
        (h1_label, h1_value), (h2_label, h2_value), (h3_label, h3_value), (h4_label, h4_value) = \
            _get_hero_4_metrics(report_type, metrics)
    
    # V4: Get core indicators for Market Snapshot
    if has_core_indicators:
        (ci1_label, ci1_value), (ci2_label, ci2_value), (ci3_label, ci3_value) = \
            _get_core_indicators(metrics)
    
    # V14: Get insight paragraph (with sender/audience-aware AI)
    insight_text = _get_insight_paragraph(
        report_type=report_type,
        area=area_display,
        metrics=metrics,
        lookback_days=lookback_days,
        filter_description=filter_description,
        sender_type=sender_type,
        total_found=total_found,
        total_shown=total_shown,
        audience_name=audience_name,
    ) if has_insight else None
    
    # Legacy: Get 3 metrics for non-V4 reports (V14: with total_shown for galleries)
    (m1_label, m1_value), (m2_label, m2_value), (m3_label, m3_value) = \
        _get_metrics_for_report_type(report_type, metrics, total_shown=total_shown)
    
    # Get extra stats if applicable (not used in V4 Market Snapshot)
    extra_stats = _get_extra_stats(report_type, metrics) if has_extra_stats else None
    
    # Get price bands if applicable
    price_bands = _get_price_bands(metrics) if has_price_bands else None
    
    # Get property type breakdown if applicable (Market Snapshot)
    property_types = _get_property_type_breakdown(metrics) if has_property_types else None
    
    # Get price tier breakdown if applicable (Market Snapshot)
    price_tiers = _get_price_tier_breakdown(metrics) if has_price_tiers else None
    
    # V5: Gallery reports - check for listings data
    has_gallery = report_type in ("new_listings_gallery", "featured_listings") and listings
    
    # V5: Listings table for inventory (and future: new_listings, closed)
    has_listings_table = config.get("has_listings_table", False) and listings
    
    # Build preheader
    preheader = _build_preheader(report_type, area_display, metrics)
    
    # V10: Quick Take (professional market insight)
    quick_take = _get_quick_take(report_type, area_display, metrics)
    
    # Build logo HTML for email header
    # Use email_logo_url if available (light version for gradient headers)
    # Otherwise, use logo_url (will be displayed on gradient, may need inversion via CSS)
    header_logo = email_logo_url or logo_url
    if header_logo:
        logo_html = f'<img src="{header_logo}" alt="{brand_name}" width="160" style="display: block; max-width: 160px; height: auto;">'
    else:
        logo_html = f'<span style="font-size: 24px; font-weight: 700; color: #ffffff;">{brand_name}</span>'
    
    # ------------------------------------------------------------------
    # V16: Build body via layout router
    # ------------------------------------------------------------------
    layout = LAYOUT_MAP.get(report_type, "market_narrative")

    if layout == "gallery":
        listing_count = len(listings) if listings else 0
        gallery_layout = _select_gallery_layout(listing_count)
        gallery_label = preset_display_name or ("New Listings" if report_type == "new_listings_gallery" else "Featured Listings")

        if gallery_layout == "single_stacked":
            body_html = _build_single_stacked_body(
                insight_text=insight_text, listings=listings or [],
                pdf_url=pdf_url, primary_color=primary_color, accent_color=accent_color,
                filter_description=filter_description,
            )
        elif gallery_layout == "gallery_2x2":
            body_html = _build_gallery_2x2_body(
                insight_text=insight_text, listings=listings or [], quick_take=quick_take,
                pdf_url=pdf_url, primary_color=primary_color, accent_color=accent_color,
                gallery_label=gallery_label, filter_description=filter_description,
            )
        elif gallery_layout == "gallery_3x2":
            body_html = _build_gallery_3x2_body(
                insight_text=insight_text, listings=listings or [], quick_take=quick_take,
                pdf_url=pdf_url, primary_color=primary_color, accent_color=accent_color,
                gallery_label=gallery_label, filter_description=filter_description,
            )
        else:
            body_html = _build_large_list_body(
                insight_text=insight_text, listings=listings or [], quick_take=quick_take,
                pdf_url=pdf_url, primary_color=primary_color, accent_color=accent_color,
                gallery_label=gallery_label, filter_description=filter_description,
            )

    elif layout == "closed_sales":
        hero_val = h1_value if has_hero_4 else m1_value
        hero_lbl = h1_label if has_hero_4 else m1_label
        secondary = []
        if has_hero_4:
            secondary = [(h2_label, h2_value), (h3_label, h3_value), (h4_label, h4_value)]
        else:
            secondary = [(m2_label, m2_value), (m3_label, m3_value)]
        body_html = _build_closed_sales_body(
            insight_text=insight_text, hero_value=hero_val, hero_label=hero_lbl,
            listings=listings or [], stats=secondary, quick_take=quick_take,
            pdf_url=pdf_url, primary_color=primary_color, accent_color=accent_color,
            filter_description=filter_description,
        )

    else:
        hero_val = h1_value if has_hero_4 else m1_value
        hero_lbl = h1_label if has_hero_4 else m1_label
        secondary = []
        if has_hero_4:
            secondary = [(h2_label, h2_value), (h3_label, h3_value), (h4_label, h4_value)]
        if has_core_indicators:
            secondary += [(ci1_label, ci1_value), (ci2_label, ci2_value), (ci3_label, ci3_value)]
        if not secondary:
            secondary = [(m1_label, m1_value), (m2_label, m2_value), (m3_label, m3_value)]
        body_html = _build_market_narrative_body(
            insight_text=insight_text, hero_value=hero_val, hero_label=hero_lbl,
            stats=secondary, quick_take=quick_take,
            pdf_url=pdf_url, primary_color=primary_color, accent_color=accent_color,
            filter_description=filter_description,
            listings=listings,
        )
    
    # ============================================================================
    # V16: Agent Footer (kept from V15 — already matches V0 email-footer.tsx)
    # ============================================================================
    
    # (old inline V4/V15 HTML builders removed — now handled by layout body builders)
    
    # V15: Build agent footer HTML - branded background, serif name, pill buttons
    if rep_photo_url and (contact_line1 or rep_name):
        # Full footer with photo - V0 design
        agent_footer_html = f'''
              <!-- V15: AGENT FOOTER (branded bg, serif, pill buttons) -->
              <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="margin-top: 4px;">
                <tr>
                  <td style="padding: 28px 0; border-top: 1px solid {primary_color}15;">
                    <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="background-color: {primary_color}08; border-radius: 10px;">
                      <tr>
                        <td style="padding: 24px;">
                          <table role="presentation" cellpadding="0" cellspacing="0">
                            <tr>
                              <!-- Agent Photo -->
                              <td style="vertical-align: top; padding-right: 20px;">
                                <!--[if mso]>
                                <v:oval xmlns:v="urn:schemas-microsoft-com:vml" style="width:80px;height:80px;" stroke="f">
                                  <v:fill type="frame" src="{rep_photo_url}"/>
                                </v:oval>
                                <![endif]-->
                                <!--[if !mso]><!-->
                                <img src="{rep_photo_url}" alt="{contact_line1 or rep_name}" width="80" height="80" style="display: block; width: 80px; height: 80px; border-radius: 50%; object-fit: cover; border: 2px solid {primary_color}33;">
                                <!--<![endif]-->
                              </td>
                              <!-- Agent Info -->
                              <td style="vertical-align: middle;">
                                <p style="margin: 0 0 2px 0; font-family: Georgia, 'Times New Roman', serif; font-size: 18px; font-weight: 700; color: #1c1917;">
                                  {contact_line1 or rep_name}
                                </p>
                                {f'<p style="margin: 0 0 12px 0; font-size: 12px; color: #78716c;">{contact_line2 or rep_title}</p>' if (contact_line2 or rep_title) else '<div style="margin-bottom: 12px;"></div>'}
                                <table role="presentation" cellpadding="0" cellspacing="0">
                                  <tr>
                                    {f"""<td style="padding-right: 8px;">
                                      <a href="tel:{rep_phone}" style="display: inline-block; padding: 6px 14px; border: 1px solid {primary_color}26; border-radius: 6px; color: {primary_color}; text-decoration: none; font-size: 12px; font-weight: 500;">
                                        {rep_phone}
                                      </a>
                                    </td>""" if rep_phone else ""}
                                    {f"""<td>
                                      <a href="mailto:{rep_email}" style="display: inline-block; padding: 6px 14px; border: 1px solid {primary_color}26; border-radius: 6px; color: {primary_color}; text-decoration: none; font-size: 12px; font-weight: 500;">
                                        {rep_email}
                                      </a>
                                    </td>""" if rep_email else ""}
                                  </tr>
                                </table>
                              </td>
                            </tr>
                          </table>
                        </td>
                      </tr>
                    </table>
                  </td>
                </tr>
              </table>'''
    elif contact_line1 or website_url:
        # Contact without photo
        agent_footer_html = f'''
              <!-- Agent Footer -->
              <table role="presentation" cellpadding="0" cellspacing="0" width="100%">
                <tr>
                  <td align="center">
                    {f'<p style="margin: 0 0 4px 0; font-size: 16px; font-weight: 600; color: #1a1a2e;">{contact_line1}</p>' if contact_line1 else ''}
                    {f'<p style="margin: 0 0 8px 0; font-size: 14px; color: #6b7280;">{contact_line2}</p>' if contact_line2 else ''}
                    {f'<a href="{website_url}" style="color: {primary_color}; text-decoration: none; font-weight: 500;">{website_url.replace("https://", "").replace("http://", "")}</a>' if website_url else ''}
                  </td>
                </tr>
              </table>'''
    else:
        # Minimal footer
        agent_footer_html = f'''
              <!-- Agent Footer -->
              <table role="presentation" cellpadding="0" cellspacing="0" width="100%">
                <tr>
                  <td align="center">
                    <p style="margin: 0; font-size: 16px; font-weight: 600; color: #1a1a2e;">{brand_name}</p>
                  </td>
                </tr>
              </table>'''
    
    # Powered by (only if not white-labeled)
    powered_by = ""
    if not brand.get("display_name"):
        powered_by = '''
                    <p style="margin: 10px 0 0 0; font-size: 11px; color: #d1d5db;">
                      Powered by TrendyReports
                    </p>'''
    
    # Build the complete HTML email
    html = f'''<!DOCTYPE html>
<html lang="en" xmlns:v="urn:schemas-microsoft-com:vml" xmlns:o="urn:schemas-microsoft-com:office:office">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta http-equiv="X-UA-Compatible" content="IE=edge">
  <meta name="x-apple-disable-message-reformatting">
  <meta name="color-scheme" content="light only">
  <meta name="supported-color-schemes" content="light only">
  <title>{brand_name} - {report_label}</title>
  
  <!--[if mso]>
  <noscript>
    <xml>
      <o:OfficeDocumentSettings>
        <o:AllowPNG/>
        <o:PixelsPerInch>96</o:PixelsPerInch>
      </o:OfficeDocumentSettings>
    </xml>
  </noscript>
  <![endif]-->
  
  <style>
    /* Reset */
    body, table, td, p, a, li {{ -webkit-text-size-adjust: 100%; -ms-text-size-adjust: 100%; }}
    table, td {{ mso-table-lspace: 0pt; mso-table-rspace: 0pt; }}
    img {{ -ms-interpolation-mode: bicubic; border: 0; height: auto; line-height: 100%; outline: none; text-decoration: none; }}
    body {{ margin: 0 !important; padding: 0 !important; width: 100% !important; }}
    
    /* Dark Mode — only adapts the outer chrome, NEVER the content card */
    @media (prefers-color-scheme: dark) {{
      .dark-bg {{ background-color: #1a1a2e !important; }}
      .dark-text {{ color: #e5e5e5 !important; }}
      .dark-border {{ border-color: #3d3d5c !important; }}
    }}
    
    /* Mobile */
    @media only screen and (max-width: 600px) {{
      .wrapper {{ width: 100% !important; }}
      .mobile-padding {{ padding: 20px !important; }}
      .mobile-stack {{ display: block !important; width: 100% !important; }}
      .mobile-center {{ text-align: center !important; }}
      .mobile-hide {{ display: none !important; }}
      .metric-card {{ display: block !important; width: 100% !important; margin-bottom: 12px !important; }}
      .band-row {{ display: block !important; width: 100% !important; }}
    }}
  </style>
</head>
<body style="margin: 0; padding: 0; background-color: #f0efed; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;">
  
  <!-- Preheader Text (hidden preview text) -->
  <div style="display: none; max-height: 0; overflow: hidden; mso-hide: all;">
    {preheader} &nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;
  </div>
  
  <!-- Email Container -->
  <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="background-color: #f0efed;" class="dark-bg">
    <tr>
      <td align="center" style="padding: 40px 20px;">
        
        <!-- Email Wrapper -->
        <table role="presentation" cellpadding="0" cellspacing="0" width="600" class="wrapper" style="max-width: 600px; width: 100%;">
          
          <!-- ========== HEADER WITH GRADIENT ========== -->
          <tr>
            <td>
              <!--[if mso]>
              <v:rect xmlns:v="urn:schemas-microsoft-com:vml" fill="true" stroke="false" style="width:600px;height:180px;">
                <v:fill type="gradient" color="{primary_color}" color2="{accent_color}" angle="135"/>
                <v:textbox inset="0,0,0,0" style="mso-fit-shape-to-text:true">
              <![endif]-->
              <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="background: linear-gradient(135deg, {primary_color} 0%, {accent_color} 100%); border-radius: 12px 12px 0 0;">
                <tr>
                  <td align="center" style="padding: 28px 40px 16px 40px;">
                    {logo_html}
                  </td>
                </tr>
                <tr>
                  <td align="center" style="padding: 0 40px 8px 40px;">
                    <!-- V8: Show brand for Market Snapshot, base report type for gallery -->
                    <span style="display: inline-block; background-color: rgba(255,255,255,0.2); color: #ffffff; font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 1.5px; padding: 6px 14px; border-radius: 20px;">
                      {brand_name if has_hero_4 else ("New Listings" if report_type == "new_listings_gallery" else "Featured Listings" if report_type == "featured_listings" else report_label)}
                    </span>
                  </td>
                </tr>
                <tr>
                  <td align="center" style="padding: 0 40px;">
                    <!-- V8: "Preset Name – Area" format for all reports -->
                    <h1 style="margin: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; font-size: 28px; font-weight: 400; color: #ffffff; line-height: 1.3; letter-spacing: -0.5px;">
                      {report_label} – {area_display}
                    </h1>
                  </td>
                </tr>
                <tr>
                  <td align="center" style="padding: 10px 40px 28px 40px;">
                    <!-- V8: Period info for all reports -->
                    <p style="margin: 0; font-size: 14px; color: rgba(255,255,255,0.9);">
                      {"Period: " + date_range + " • Source: Live MLS Data" if has_hero_4 else (date_range + " • Live MLS Data")}
                    </p>
                  </td>
                </tr>
              </table>
              <!--[if mso]>
                </v:textbox>
              </v:rect>
              <![endif]-->
            </td>
          </tr>
          
          <!-- Accent Transition Strip -->
          <tr>
            <td style="height: 4px; background: linear-gradient(90deg, {primary_color} 0%, {accent_color} 100%); font-size: 0; line-height: 0;">&nbsp;</td>
          </tr>
          
          <!-- ========== MAIN CONTENT (V16: Layout-based body) ========== -->
          <tr>
            <td style="background-color: #ffffff; padding: 40px;" class="mobile-padding">
              
              {_build_section_label(section_label, primary_color) if section_label else ""}

{body_html}

              <!-- Divider before agent footer -->
              <table role="presentation" cellpadding="0" cellspacing="0" width="100%">
                <tr>
                  <td style="border-top: 1px solid {primary_color}20; padding-top: 32px;" class="dark-border"></td>
                </tr>
              </table>
              
{agent_footer_html}
              
            </td>
          </tr>
          
          <!-- ========== FOOTER ========== -->
          <tr>
            <td style="background-color: #fafaf9; padding: 24px 40px; border-radius: 0 0 12px 12px; border-top: 1px solid #e5e7eb;" class="dark-border mobile-padding">
              <table role="presentation" cellpadding="0" cellspacing="0" width="100%">
                <tr>
                  <td align="center">
                    <p style="margin: 0 0 8px 0; font-size: 13px; color: #9ca3af;">
                      {f'Powered by <a href="{website_url or "#"}" style="color: {primary_color}; text-decoration: none; font-weight: 500;">{brand_name}</a>' if brand.get("display_name") else f'Powered by <span style="color: {primary_color}; font-weight: 500;">TrendyReports</span>'}
                    </p>
                    <p style="margin: 0; font-size: 12px; color: #9ca3af;">
                      <a href="{unsubscribe_url}" style="color: #9ca3af; text-decoration: underline;">Unsubscribe</a>
                      from these notifications
                    </p>
                  </td>
                </tr>
              </table>
            </td>
          </tr>
          
        </table>
        <!-- End Wrapper -->
        
      </td>
    </tr>
  </table>
  <!-- End Container -->
  
</body>
</html>'''
    
    return html


def schedule_email_subject(
    report_type: str, 
    city: Optional[str], 
    zip_codes: Optional[list]
) -> str:
    """Generate email subject line for a scheduled report."""
    # Get report label
    config = REPORT_CONFIG.get(report_type, {})
    report_label = config.get("label", report_type.replace("_", " ").title())
    
    # Format area
    if city:
        area = city
    elif zip_codes and len(zip_codes) > 0:
        if len(zip_codes) == 1:
            area = f"ZIP {zip_codes[0]}"
        else:
            area = f"{len(zip_codes)} ZIP codes"
    else:
        area = "Your Area"
    
    return f"📊 Your {report_label} for {area} is Ready!"
