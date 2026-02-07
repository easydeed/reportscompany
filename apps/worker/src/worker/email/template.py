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


def _build_vertical_list_html(listings: List[Dict], primary_color: str, accent_color: str) -> str:
    """
    V10: Build email-safe HTML for vertical list layout (image left, info right).
    Used for odd/awkward listing counts (1, 5, 7, 8, 10+) to avoid broken grids.
    
    Professional styling with clean typography and neutral colors.
    """
    rows_html = ""
    
    for i, listing in enumerate(listings):
        photo_url = listing.get("hero_photo_url") or ""
        address = listing.get("street_address") or "Address Not Available"
        city = listing.get("city") or ""
        zip_code = listing.get("zip_code") or ""
        price = listing.get("list_price")
        beds = listing.get("bedrooms")
        baths = listing.get("bathrooms")
        sqft = listing.get("sqft")
        
        # Format price
        if price:
            if price >= 1_000_000:
                price_str = f"${price / 1_000_000:.2f}M"
            else:
                price_str = f"${price:,.0f}"
        else:
            price_str = "Price N/A"
        
        # Format details
        details_parts = []
        if beds:
            details_parts.append(f"{beds} Bed")
        if baths:
            details_parts.append(f"{baths} Bath")
        if sqft:
            details_parts.append(f"{sqft:,} SF")
        details_str = " • ".join(details_parts) if details_parts else ""
        
        # Location
        location = f"{city}, {zip_code}" if zip_code else city
        
        # Placeholder if no photo
        if photo_url:
            photo_html = f'<img src="{photo_url}" alt="{address}" width="130" height="95" style="display: block; width: 130px; height: 95px; object-fit: cover; border-radius: 4px; background: #e2e8f0;">'
        else:
            photo_html = '<div style="width: 130px; height: 95px; background: #f5f5f4; border-radius: 4px; display: flex; align-items: center; justify-content: center;"><span style="color: #a8a29e; font-size: 10px;">No Photo</span></div>'
        
        # Row border (not on last item)
        border_style = "border-bottom: 1px solid #e7e5e4;" if i < len(listings) - 1 else ""
        
        # V15: Build brand-tinted detail badges for vertical list
        badges_html = ""
        if beds:
            badges_html += f'<span style="display: inline-block; padding: 3px 8px; background-color: {primary_color}12; border-radius: 4px; font-size: 10px; font-weight: 500; color: {primary_color}; margin-right: 4px;">{beds} Bed</span>'
        if baths:
            badges_html += f'<span style="display: inline-block; padding: 3px 8px; background-color: {primary_color}12; border-radius: 4px; font-size: 10px; font-weight: 500; color: {primary_color}; margin-right: 4px;">{baths} Bath</span>'
        if sqft:
            badges_html += f'<span style="display: inline-block; padding: 3px 8px; background-color: {primary_color}12; border-radius: 4px; font-size: 10px; font-weight: 500; color: {primary_color};">{sqft:,} SF</span>'
        
        rows_html += f'''
                      <tr>
                        <td style="padding: 14px 16px; {border_style}">
                          <table role="presentation" cellpadding="0" cellspacing="0" width="100%">
                            <tr>
                              <td width="146" style="vertical-align: top; padding-right: 16px;">
                                {photo_html}
                              </td>
                              <td style="vertical-align: top;">
                                <p style="margin: 0 0 6px 0; font-family: Georgia, 'Times New Roman', serif; font-size: 17px; font-weight: 700; color: {primary_color};">
                                  {price_str}
                                </p>
                                <p style="margin: 0 0 3px 0; font-size: 15px; font-weight: 600; color: #1c1917;">
                                  {address}
                                </p>
                                <p style="margin: 0 0 8px 0; font-size: 12px; font-weight: 400; color: #78716c;">
                                  {location}
                                </p>
                                {f'<p style="margin: 0;">{badges_html}</p>' if badges_html else ''}
                              </td>
                            </tr>
                          </table>
                        </td>
                      </tr>'''
    
    return f'''
                    <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="background-color: #ffffff; border-radius: 8px; border: 1px solid #e7e5e4;">
                      {rows_html}
                    </table>'''


def _build_gallery_grid_html(listings: List[Dict], report_type: str, primary_color: str, accent_color: str = None, preset_display_name: str = None) -> str:
    """
    Build email-safe HTML for photo gallery with adaptive layouts.
    
    V8: Adaptive layouts based on listing count:
    - 3, 6, 9 listings → 3-column grid
    - 2, 4 listings → 2-column grid  
    - 1, 5, 7, 8, 10+ listings → Vertical list (image left, info right)
    
    Uses table layout for maximum email client compatibility.
    """
    accent_color = accent_color or primary_color
    if not listings:
        return ""
    
    # V12: Increased from 9 to 12 max for more comprehensive email galleries
    # This allows for 4×3 grid layouts while keeping emails manageable
    listings = listings[:12]
    count = len(listings)
    
    # Determine layout based on count
    # Clean grid layouts: 3, 6, 9, 12 (3-col) or 2, 4 (2-col)
    # Awkward counts that create broken grids: 1, 5, 7, 8, 10, 11 → use vertical list
    if count in (3, 6, 9, 12):
        cols = 3
        use_grid = True
    elif count in (2, 4):
        cols = 2
        use_grid = True
    else:
        # 1, 5, 7, 8, 10, 11 → vertical list (looks cleaner than broken grids)
        use_grid = False
    
    # Build section header - V6: Use preset_display_name if provided
    if preset_display_name:
        section_title = preset_display_name
    else:
        section_title = "New Listings"
    
    # V15: Gallery count badge (V0 design - branded pill + line separator)
    section_header_style = ""  # Not used - replaced by count badge below
    count_style = ""
    title_style = ""
    
    # Build the content section
    if use_grid:
        # Grid layout
        cards_html = ""
        for i, listing in enumerate(listings):
            photo_url = listing.get("hero_photo_url") or ""
            address = listing.get("street_address") or "Address Not Available"
            city = listing.get("city") or ""
            zip_code = listing.get("zip_code") or ""
            price = listing.get("list_price")
            beds = listing.get("bedrooms")
            baths = listing.get("bathrooms")
            sqft = listing.get("sqft")
            
            # Format price
            if price:
                if price >= 1_000_000:
                    price_str = f"${price / 1_000_000:.2f}M"
                else:
                    price_str = f"${price:,.0f}"
            else:
                price_str = "Price N/A"
            
            # Format details
            details_parts = []
            if beds:
                details_parts.append(f"{beds} Bed")
            if baths:
                details_parts.append(f"{baths} Bath")
            if sqft:
                details_parts.append(f"{sqft:,} SF")
            details_str = " • ".join(details_parts) if details_parts else ""
            
            # Location
            location = f"{city}, {zip_code}" if zip_code else city
            
            # Card dimensions based on columns
            card_width = "50%" if cols == 2 else "33%"
            img_height = "140" if cols == 2 else "110"
            content_height = "85" if cols == 2 else "75"
            
            # Placeholder if no photo
            if photo_url:
                photo_html = f'<img src="{photo_url}" alt="{address}" width="100%" height="{img_height}" style="display: block; width: 100%; height: {img_height}px; object-fit: cover; background: #f5f5f4;">'
            else:
                photo_html = f'<div style="width: 100%; height: {img_height}px; background: #f5f5f4; display: flex; align-items: center; justify-content: center;"><span style="color: #a8a29e; font-size: 11px;">No Photo</span></div>'
            
            # Start new row
            if i % cols == 0:
                if i > 0:
                    cards_html += "</tr>"
                cards_html += "<tr>"
            
            # V15: Build brand-tinted detail badges
            badges_html = ""
            if beds:
                badges_html += f'<span style="display: inline-block; padding: 3px 8px; background-color: {primary_color}12; border-radius: 4px; font-size: 10px; font-weight: 500; color: {primary_color}; margin-right: 4px;">{beds} Bed</span>'
            if baths:
                badges_html += f'<span style="display: inline-block; padding: 3px 8px; background-color: {primary_color}12; border-radius: 4px; font-size: 10px; font-weight: 500; color: {primary_color}; margin-right: 4px;">{baths} Bath</span>'
            if sqft:
                badges_html += f'<span style="display: inline-block; padding: 3px 8px; background-color: {primary_color}12; border-radius: 4px; font-size: 10px; font-weight: 500; color: {primary_color};">{sqft:,} SF</span>'
            
            cards_html += f'''
                      <td width="{card_width}" style="padding: 5px; vertical-align: top;">
                        <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="background-color: #ffffff; border-radius: 8px; border: 1px solid #e7e5e4; overflow: hidden;">
                          <tr>
                            <td style="padding: 0;">
                              {photo_html}
                            </td>
                          </tr>
                          <tr>
                            <td style="padding: 10px 12px; height: {content_height}px; vertical-align: top;">
                              <p style="margin: 0 0 6px 0; font-family: Georgia, 'Times New Roman', serif; font-size: 16px; font-weight: 700; color: {primary_color};">
                                {price_str}
                              </p>
                              <p style="margin: 0 0 2px 0; font-size: 13px; font-weight: 600; color: #1c1917; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
                                {address}
                              </p>
                              <p style="margin: 0 0 6px 0; font-size: 11px; font-weight: 400; color: #78716c; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
                                {location}
                              </p>
                              {f'<p style="margin: 0;">{badges_html}</p>' if badges_html else ''}
                            </td>
                          </tr>
                        </table>
                      </td>'''
        
        # Close last row (no need to pad - counts are always divisible)
        if listings:
            cards_html += "</tr>"
        
        content_html = f'''
                    <table role="presentation" cellpadding="0" cellspacing="0" width="100%">
                      {cards_html}
                    </table>'''
    else:
        # Vertical list layout
        content_html = _build_vertical_list_html(listings, primary_color, accent_color)
    
    return f'''
              <!-- V15: Photo Gallery (branded count badge + adaptive layout) -->
              <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="margin-bottom: 24px;">
                <tr>
                  <td style="padding-bottom: 16px;">
                    <table role="presentation" cellpadding="0" cellspacing="0" width="100%">
                      <tr>
                        <td width="auto" style="vertical-align: middle;">
                          <span style="display: inline-block; background-color: {primary_color}; color: #ffffff; font-size: 14px; font-weight: 700; padding: 6px 16px; border-radius: 20px;">
                            {count}
                          </span>
                        </td>
                        <td style="padding-left: 10px; vertical-align: middle;">
                          <span style="font-size: 14px; font-weight: 600; color: #1c1917;">{section_title}</span>
                        </td>
                        <td style="vertical-align: middle; padding-left: 12px;">
                          <div style="height: 1px; background-color: #e7e5e4;"></div>
                        </td>
                      </tr>
                    </table>
                  </td>
                </tr>
                <tr>
                  <td>
                    {content_html}
                  </td>
                </tr>
              </table>
'''


def _build_listings_table_html(listings: List[Dict], report_type: str, primary_color: str) -> str:
    """
    Build email-safe HTML table for listings (inventory, new_listings, closed).
    
    Shows: Address, Beds, Baths, Price
    Limited to 10 rows for email practicality.
    
    Uses table layout for maximum email client compatibility.
    """
    if not listings:
        return ""
    
    # Limit to 10 listings for email
    listings = listings[:10]
    
    # Build table rows
    rows_html = ""
    for i, listing in enumerate(listings):
        address = listing.get("street_address") or "Address Not Available"
        city = listing.get("city") or ""
        beds = listing.get("bedrooms") or "-"
        baths = listing.get("bathrooms") or "-"
        price = listing.get("list_price")
        
        # Format price
        if price:
            if price >= 1_000_000:
                price_str = f"${price / 1_000_000:.2f}M"
            else:
                price_str = f"${price:,.0f}"
        else:
            price_str = "-"
        
        # Alternate row background
        bg_color = "#fafaf9" if i % 2 == 0 else "#ffffff"
        
        # V15: Get sqft for additional context
        sqft = listing.get("sqft")
        sqft_str = f" &middot; {sqft:,} SF" if sqft else ""
        
        rows_html += f'''
                      <tr style="background-color: {bg_color};">
                        <td style="padding: 10px 12px; border-bottom: 1px solid #e7e5e4;">
                          <span style="font-size: 13px; font-weight: 600; color: #1c1917;">{address}</span>
                          <br/>
                          <span style="font-size: 11px; color: #78716c;">{city}{sqft_str}</span>
                        </td>
                        <td align="center" style="padding: 10px 8px; border-bottom: 1px solid #e7e5e4; font-size: 13px; color: #44403c;">
                          {beds}/{baths}
                        </td>
                        <td align="right" style="padding: 10px 12px; border-bottom: 1px solid #e7e5e4;">
                          <span style="font-family: Georgia, 'Times New Roman', serif; font-size: 14px; font-weight: 700; color: {primary_color};">
                            {price_str}
                          </span>
                        </td>
                      </tr>'''
    
    # Determine section title based on report type
    titles = {
        "inventory": "Active Listings",
        "new_listings": "New Listings",
        "closed": "Recently Sold",
    }
    section_title = titles.get(report_type, "Listings")
    
    # V15: Build summary stats row (V0 table-view design)
    # Calculate summary stats from listings
    prices = [l.get("list_price", 0) for l in listings if l.get("list_price")]
    avg_price = sum(prices) / len(prices) if prices else 0
    total_sales = len(listings)
    
    summary_stats_html = ""
    if prices:
        avg_price_str = _format_price_clean(avg_price)
        summary_stats_html = f'''
                <tr>
                  <td style="padding-bottom: 16px;">
                    <table role="presentation" cellpadding="0" cellspacing="0" width="100%">
                      <tr>
                        <td width="50%" style="padding-right: 4px;">
                          <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="border: 1px solid #e7e5e4; border-radius: 8px;">
                            <tr>
                              <td align="center" style="padding: 12px 6px;">
                                <p style="margin: 0; font-family: Georgia, 'Times New Roman', serif; font-size: 18px; font-weight: 700; color: {primary_color};">{total_sales}</p>
                                <p style="margin: 4px 0 0; font-size: 9px; font-weight: 600; color: #78716c; text-transform: uppercase; letter-spacing: 0.5px;">Total</p>
                              </td>
                            </tr>
                          </table>
                        </td>
                        <td width="50%" style="padding-left: 4px;">
                          <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="border: 1px solid #e7e5e4; border-radius: 8px;">
                            <tr>
                              <td align="center" style="padding: 12px 6px;">
                                <p style="margin: 0; font-family: Georgia, 'Times New Roman', serif; font-size: 18px; font-weight: 700; color: {primary_color};">{avg_price_str}</p>
                                <p style="margin: 4px 0 0; font-size: 9px; font-weight: 600; color: #78716c; text-transform: uppercase; letter-spacing: 0.5px;">Avg Price</p>
                              </td>
                            </tr>
                          </table>
                        </td>
                      </tr>
                    </table>
                  </td>
                </tr>'''
    
    return f'''
              <!-- V15: Listings Table (brand header + summary stats) -->
              <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="margin-bottom: 24px;">
                <tr>
                  <td style="padding-bottom: 12px;">
                    {_section_label_html(f"{section_title} (Top {len(listings)})", primary_color)}
                  </td>
                </tr>
                {summary_stats_html}
                <tr>
                  <td>
                    <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="background-color: #ffffff; border-radius: 8px; border: 1px solid #e7e5e4; overflow: hidden;">
                      <!-- V15: Brand-colored header row -->
                      <tr style="background-color: {primary_color};">
                        <td style="padding: 10px 12px; font-size: 10px; font-weight: 700; color: #ffffff; text-transform: uppercase; letter-spacing: 0.5px;">
                          Address
                        </td>
                        <td align="center" style="padding: 10px 8px; font-size: 10px; font-weight: 700; color: #ffffff; text-transform: uppercase; letter-spacing: 0.5px; width: 50px;">
                          Bd/Ba
                        </td>
                        <td align="right" style="padding: 10px 12px; font-size: 10px; font-weight: 700; color: #ffffff; text-transform: uppercase; letter-spacing: 0.5px; width: 100px;">
                          Price
                        </td>
                      </tr>
                      {rows_html}
                    </table>
                  </td>
                </tr>
              </table>
'''


def _build_kpi_card_html(label: str, value: str, change: str, positive: bool, position: int) -> str:
    """
    V15: Build a single KPI card with trend indicator (V0 StatCard design).
    Used in 2×2 grid for analytics-style layouts.
    
    Args:
        label: KPI label (e.g. "Median Price")
        value: Display value (e.g. "$875K")
        change: Change string (e.g. "+8.0%")
        positive: Whether the change is positive (green) or negative (red)
        position: 0-3 position in 2×2 grid (controls padding)
    """
    padding = "0 4px 8px 0" if position % 2 == 0 else "0 0 8px 4px"
    arrow = "&#9650;" if positive else "&#9660;"  # ▲ or ▼
    color = "#059669" if positive else "#dc2626"
    
    return f'''<td width="50%" style="padding: {padding};">
  <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="border: 1px solid #e7e5e4; border-radius: 8px;">
    <tr>
      <td style="padding: 16px;">
        <p style="margin: 0 0 6px; font-size: 10px; font-weight: 600; color: #78716c; text-transform: uppercase; letter-spacing: 0.5px;">{label}</p>
        <p style="margin: 0 0 8px; font-family: Georgia, 'Times New Roman', serif; font-size: 24px; font-weight: 700; color: #1c1917;">{value}</p>
        <p style="margin: 0; font-size: 11px;">
          <span style="color: {color}; font-weight: 600;">{arrow} {change}</span>
          <span style="color: #78716c;"> vs last yr</span>
        </p>
      </td>
    </tr>
  </table>
</td>'''


def _build_yoy_comparison_table_html(rows: list, primary_color: str) -> str:
    """
    V15: Build Year-over-Year comparison table (V0 design).
    
    Args:
        rows: List of dicts with keys: metric, last, current, change, positive
        primary_color: Brand primary color
    """
    if not rows:
        return ""
    
    table_rows = ""
    for i, row in enumerate(rows):
        bg = "" if i % 2 == 0 else f' style="background-color: #fafaf9;"'
        arrow = "&#9650;" if row.get("positive") else "&#9660;"
        color = "#059669" if row.get("positive") else "#dc2626"
        table_rows += f'''
            <tr{bg}>
              <td style="padding: 10px 12px; border-bottom: 1px solid #e7e5e4; font-size: 12px; font-weight: 600; color: #1c1917;">{row["metric"]}</td>
              <td align="center" style="padding: 10px 8px; border-bottom: 1px solid #e7e5e4; font-size: 12px; color: #78716c;">{row["last"]}</td>
              <td align="center" style="padding: 10px 8px; border-bottom: 1px solid #e7e5e4; font-size: 12px; font-weight: 600; color: #1c1917;">{row["current"]}</td>
              <td align="center" style="padding: 10px 8px; border-bottom: 1px solid #e7e5e4; font-size: 12px; font-weight: 600; color: {color};">{arrow} {row["change"]}</td>
            </tr>'''
    
    return f'''
              <!-- V15: Year-over-Year Comparison Table -->
              <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="margin-bottom: 28px;">
                <tr>
                  <td>
                    {_section_label_html("Year-over-Year Comparison", primary_color)}
                    <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="border: 1px solid #e7e5e4; border-radius: 8px; overflow: hidden;">
                      <tr style="background-color: {primary_color};">
                        <td style="padding: 10px 12px; font-size: 10px; font-weight: 700; color: #ffffff; text-transform: uppercase; letter-spacing: 0.5px;">Metric</td>
                        <td align="center" style="padding: 10px 8px; font-size: 10px; font-weight: 700; color: #ffffff; text-transform: uppercase; letter-spacing: 0.5px;">Last Year</td>
                        <td align="center" style="padding: 10px 8px; font-size: 10px; font-weight: 700; color: #ffffff; text-transform: uppercase; letter-spacing: 0.5px;">This Year</td>
                        <td align="center" style="padding: 10px 8px; font-size: 10px; font-weight: 700; color: #ffffff; text-transform: uppercase; letter-spacing: 0.5px;">Change</td>
                      </tr>
                      {table_rows}
                    </table>
                  </td>
                </tr>
              </table>'''


def _section_label_html(label: str, primary_color: str) -> str:
    """V15: Branded section label with accent bar (matches V0 SectionLabel component)."""
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
    
    # Build extra stats HTML (legacy V3)
    extra_stats_html = ""
    if extra_stats:
        (es1_value, es1_label), (es2_value, es2_label) = extra_stats
        extra_stats_html = f'''
              <!-- Extra Stats Row -->
              <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="margin-bottom: 20px; background-color: #f8fafc; border-radius: 10px; border: 1px solid #e2e8f0;">
                <tr>
                  <td align="center" style="padding: 16px 24px;">
                    <span style="font-size: 14px; color: #475569;">
                      <strong style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; font-size: 16px; color: #1e293b;">{es1_value}</strong>
                      <span style="color: #64748b;"> {es1_label}</span>
                      &nbsp;&nbsp;<span style="color: #cbd5e1;">|</span>&nbsp;&nbsp;
                      <strong style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; font-size: 16px; color: #1e293b;">{es2_value}</strong>
                      <span style="color: #64748b;"> {es2_label}</span>
                    </span>
                  </td>
                </tr>
              </table>
'''
    
    # ============================================================================
    # V4 HTML SECTIONS (Market Snapshot)
    # ============================================================================
    
    # V15: Insight Paragraph - Branded left border (V0 design)
    insight_html = ""
    if insight_text:
        insight_html = f'''
              <!-- V15: AI Insight (branded left border) -->
              <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="margin-bottom: 28px;">
                <tr>
                  <td style="padding: 16px 20px; background-color: {primary_color}0A; border-left: 4px solid {primary_color}; border-radius: 8px;">
                    <p style="margin: 0; font-size: 14px; line-height: 1.6; color: #44403c; font-weight: 400;">
                      {insight_text}
                    </p>
                  </td>
                </tr>
              </table>
'''
    
    # V11: Filter Description Blurb - Shows preset/audience filter details
    filter_description_html = ""
    if filter_description:
        filter_description_html = f'''
              <!-- V11: Filter Description Blurb -->
              <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="margin-bottom: 20px;">
                <tr>
                  <td align="center" style="padding: 12px 16px; background: linear-gradient(135deg, {primary_color}08 0%, {accent_color}08 100%); border-radius: 8px; border-left: 3px solid {primary_color};">
                    <p style="margin: 0; font-size: 13px; line-height: 1.5; color: #44403c;">
                      <span style="font-weight: 600; color: {primary_color};">Report Criteria:</span> {filter_description}
                    </p>
                  </td>
                </tr>
              </table>
'''
    
    # V10: Professional Market Snapshot Redesign - Clean, Corporate Layout
    # For market_snapshot: Refined visual design with clear data hierarchy
    # For other report types: Use standard 4-metric row layout
    hero_4_html = ""
    if has_hero_4:
        if report_type == "market_snapshot":
            # V15: Market Snapshot - Branded hero metric card + 3 separate metric cards (V0 design)
            hero_4_html = f'''
              <!-- V15: HERO METRIC (branded tinted card, serif font) -->
              <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="margin-bottom: 28px;">
                <tr>
                  <td align="center" style="padding: 24px 20px; background-color: {primary_color}0F; border-radius: 12px; border: 1px solid {primary_color}1A;">
                    <p style="margin: 0 0 6px 0; font-size: 11px; font-weight: 600; color: {primary_color}B3; text-transform: uppercase; letter-spacing: 2px;">
                      {h1_label}
                    </p>
                    <p style="margin: 0; font-family: Georgia, 'Times New Roman', serif; font-size: 48px; font-weight: 700; color: {primary_color}; letter-spacing: -1px; line-height: 1;">
                      {h1_value}
                    </p>
                    <!--[if !mso]><!-->
                    <div style="margin: 12px auto 0; width: 48px; height: 4px; border-radius: 4px; background-color: {accent_color};"></div>
                    <!--<![endif]-->
                  </td>
                </tr>
              </table>
              
              <!-- V15: KEY METRICS ROW (3 separate cards with accent dots, serif numbers) -->
              <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="margin-bottom: 28px;">
                <tr>
                  <td width="33%" style="padding-right: 6px;">
                    <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="border: 1px solid #e7e5e4; border-radius: 8px; background-color: #ffffff;">
                      <tr>
                        <td align="center" style="padding: 18px 8px;">
                          <p style="margin: 0 0 6px 0; font-size: 14px; color: {accent_color};">&#9679;</p>
                          <p style="margin: 0 0 4px 0; font-family: Georgia, 'Times New Roman', serif; font-size: 24px; font-weight: 700; color: #1c1917;">
                            {h2_value}
                          </p>
                          <p style="margin: 0; font-size: 10px; font-weight: 600; color: #78716c; text-transform: uppercase; letter-spacing: 0.5px;">
                            {h2_label}
                          </p>
                        </td>
                      </tr>
                    </table>
                  </td>
                  <td width="34%" style="padding: 0 3px;">
                    <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="border: 1px solid #e7e5e4; border-radius: 8px; background-color: #ffffff;">
                      <tr>
                        <td align="center" style="padding: 18px 8px;">
                          <p style="margin: 0 0 6px 0; font-size: 14px; color: {accent_color};">&#9679;</p>
                          <p style="margin: 0 0 4px 0; font-family: Georgia, 'Times New Roman', serif; font-size: 24px; font-weight: 700; color: #1c1917;">
                            {h3_value}
                          </p>
                          <p style="margin: 0; font-size: 10px; font-weight: 600; color: #78716c; text-transform: uppercase; letter-spacing: 0.5px;">
                            {h3_label}
                          </p>
                        </td>
                      </tr>
                    </table>
                  </td>
                  <td width="33%" style="padding-left: 6px;">
                    <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="border: 1px solid #e7e5e4; border-radius: 8px; background-color: #ffffff;">
                      <tr>
                        <td align="center" style="padding: 18px 8px;">
                          <p style="margin: 0 0 6px 0; font-size: 14px; color: {accent_color};">&#9679;</p>
                          <p style="margin: 0 0 4px 0; font-family: Georgia, 'Times New Roman', serif; font-size: 24px; font-weight: 700; color: #1c1917;">
                            {h4_value}
                          </p>
                          <p style="margin: 0; font-size: 10px; font-weight: 600; color: #78716c; text-transform: uppercase; letter-spacing: 0.5px;">
                            {h4_label}
                          </p>
                        </td>
                      </tr>
                    </table>
                  </td>
                </tr>
              </table>
'''
        else:
            # V15: Non-Market Snapshot reports - Same branded hero + 3 card layout
            hero_4_html = f'''
              <!-- V15: HERO METRIC (branded tinted card, serif font) -->
              <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="margin-bottom: 28px;">
                <tr>
                  <td align="center" style="padding: 24px 20px; background-color: {primary_color}0F; border-radius: 12px; border: 1px solid {primary_color}1A;">
                    <p style="margin: 0 0 6px 0; font-size: 11px; font-weight: 600; color: {primary_color}B3; text-transform: uppercase; letter-spacing: 2px;">
                      {h1_label}
                    </p>
                    <p style="margin: 0; font-family: Georgia, 'Times New Roman', serif; font-size: 48px; font-weight: 700; color: {primary_color}; letter-spacing: -1px; line-height: 1;">
                      {h1_value}
                    </p>
                    <!--[if !mso]><!-->
                    <div style="margin: 12px auto 0; width: 48px; height: 4px; border-radius: 4px; background-color: {accent_color};"></div>
                    <!--<![endif]-->
                  </td>
                </tr>
              </table>
              
              <!-- V15: KEY METRICS ROW (3 separate cards with accent dots, serif numbers) -->
              <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="margin-bottom: 28px;">
                <tr>
                  <td width="33%" style="padding-right: 6px;">
                    <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="border: 1px solid #e7e5e4; border-radius: 8px; background-color: #ffffff;">
                      <tr>
                        <td align="center" style="padding: 18px 8px;">
                          <p style="margin: 0 0 6px 0; font-size: 14px; color: {accent_color};">&#9679;</p>
                          <p style="margin: 0 0 4px 0; font-family: Georgia, 'Times New Roman', serif; font-size: 24px; font-weight: 700; color: #1c1917;">
                            {h2_value}
                          </p>
                          <p style="margin: 0; font-size: 10px; font-weight: 600; color: #78716c; text-transform: uppercase; letter-spacing: 0.5px;">
                            {h2_label}
                          </p>
                        </td>
                      </tr>
                    </table>
                  </td>
                  <td width="34%" style="padding: 0 3px;">
                    <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="border: 1px solid #e7e5e4; border-radius: 8px; background-color: #ffffff;">
                      <tr>
                        <td align="center" style="padding: 18px 8px;">
                          <p style="margin: 0 0 6px 0; font-size: 14px; color: {accent_color};">&#9679;</p>
                          <p style="margin: 0 0 4px 0; font-family: Georgia, 'Times New Roman', serif; font-size: 24px; font-weight: 700; color: #1c1917;">
                            {h3_value}
                          </p>
                          <p style="margin: 0; font-size: 10px; font-weight: 600; color: #78716c; text-transform: uppercase; letter-spacing: 0.5px;">
                            {h3_label}
                          </p>
                        </td>
                      </tr>
                    </table>
                  </td>
                  <td width="33%" style="padding-left: 6px;">
                    <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="border: 1px solid #e7e5e4; border-radius: 8px; background-color: #ffffff;">
                      <tr>
                        <td align="center" style="padding: 18px 8px;">
                          <p style="margin: 0 0 6px 0; font-size: 14px; color: {accent_color};">&#9679;</p>
                          <p style="margin: 0 0 4px 0; font-family: Georgia, 'Times New Roman', serif; font-size: 24px; font-weight: 700; color: #1c1917;">
                            {h4_value}
                          </p>
                          <p style="margin: 0; font-size: 10px; font-weight: 600; color: #78716c; text-transform: uppercase; letter-spacing: 0.5px;">
                            {h4_label}
                          </p>
                        </td>
                      </tr>
                    </table>
                  </td>
                </tr>
              </table>
'''
    
    # V15: Redesigned Core Indicators - Branded section label + accent dots
    core_indicators_html = ""
    if has_core_indicators:
        core_indicators_html = f'''
              <!-- V15: MARKET ACTIVITY - Branded label + accent dots -->
              <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="margin-bottom: 24px;">
                <tr>
                  <td style="padding: 20px; background-color: #ffffff; border-radius: 8px; border: 1px solid #e7e5e4;">
                    {_section_label_html("Market Activity", primary_color)}
                    <table role="presentation" cellpadding="0" cellspacing="0" width="100%">
                      <tr>
                        <td width="33%" align="center" style="vertical-align: top; padding: 8px 4px;">
                          <p style="margin: 0 0 4px 0; font-size: 12px; color: {primary_color}80;">&#8226;</p>
                          <p style="margin: 0 0 2px 0; font-family: Georgia, 'Times New Roman', serif; font-size: 22px; font-weight: 700; color: #1c1917;">
                            {ci1_value}
                          </p>
                          <p style="margin: 0; font-size: 10px; font-weight: 500; color: #78716c; text-transform: uppercase; letter-spacing: 0.5px;">
                            {ci1_label}
                          </p>
                        </td>
                        <td width="34%" align="center" style="vertical-align: top; padding: 8px 4px; border-left: 1px solid #e7e5e4; border-right: 1px solid #e7e5e4;">
                          <p style="margin: 0 0 4px 0; font-size: 12px; color: {primary_color}80;">&#8226;</p>
                          <p style="margin: 0 0 2px 0; font-family: Georgia, 'Times New Roman', serif; font-size: 22px; font-weight: 700; color: #1c1917;">
                            {ci2_value}
                          </p>
                          <p style="margin: 0; font-size: 10px; font-weight: 500; color: #78716c; text-transform: uppercase; letter-spacing: 0.5px;">
                            {ci2_label}
                          </p>
                        </td>
                        <td width="33%" align="center" style="vertical-align: top; padding: 8px 4px;">
                          <p style="margin: 0 0 4px 0; font-size: 12px; color: {primary_color}80;">&#8226;</p>
                          <p style="margin: 0 0 2px 0; font-family: Georgia, 'Times New Roman', serif; font-size: 22px; font-weight: 700; color: #1c1917;">
                            {ci3_value}
                          </p>
                          <p style="margin: 0; font-size: 10px; font-weight: 500; color: #78716c; text-transform: uppercase; letter-spacing: 0.5px;">
                            {ci3_label}
                          </p>
                        </td>
                      </tr>
                    </table>
                  </td>
                </tr>
              </table>
'''
    
    # Build price bands HTML - monochromatic design using primary_color only
    price_bands_html = ""
    if price_bands:
        bands_rows = ""
        for i, band in enumerate(price_bands):
            # All bands use primary_color for monochromatic design
            color = primary_color
            
            border = 'border-bottom: 1px solid #e7e5e4;' if i < len(price_bands) - 1 else ''
            bands_rows += f'''
                <!-- {band["name"]} -->
                <tr>
                  <td class="band-row" style="padding: 10px 0; {border}">
                    <table role="presentation" cellpadding="0" cellspacing="0" width="100%">
                      <tr>
                        <td width="12" style="vertical-align: middle;">
                          <div style="width: 10px; height: 10px; background-color: {color}; border-radius: 50%;"></div>
                        </td>
                        <td style="padding-left: 12px; vertical-align: middle;">
                          <span style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; font-size: 15px; font-weight: 600; color: #292524;">{band["name"]}</span>
                          <span style="font-size: 13px; color: #78716c; margin-left: 8px;">{band["range"]}</span>
                        </td>
                        <td align="right" style="vertical-align: middle;">
                          <span style="font-size: 15px; font-weight: 900; color: #1c1917;">{band["count"]} listings</span>
                        </td>
                      </tr>
                    </table>
                  </td>
                </tr>
'''
        
        price_bands_html = f'''
              <!-- Price Bands Section -->
              <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="margin-bottom: 24px;">
                <tr>
                  <td style="padding-bottom: 12px;">
                    <p style="margin: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; font-size: 13px; font-weight: 600; color: #57534e; text-transform: uppercase; letter-spacing: 1px;">
                      Price Tiers
                    </p>
                  </td>
                </tr>
                {bands_rows}
              </table>
'''
    
    # V15: Property Types + Price Tiers side-by-side (V0 design)
    property_types_html = ""
    price_tiers_html = ""
    
    if property_types and price_tiers:
        # Build property type rows (vertical list with icons)
        property_type_rows = ""
        for ptype in property_types:
            property_type_rows += f'''
                              <tr>
                                <td style="padding: 5px 0;">
                                  <table role="presentation" cellpadding="0" cellspacing="0" width="100%">
                                    <tr>
                                      <td style="vertical-align: middle;">
                                        <span style="font-size: 14px; color: {primary_color}40;">&#9632;</span>
                                        <span style="font-size: 13px; color: #1c1917; padding-left: 6px;">{ptype["name"]}</span>
                                      </td>
                                      <td align="right" style="vertical-align: middle;">
                                        <span style="font-family: Georgia, 'Times New Roman', serif; font-size: 14px; font-weight: 700; color: #1c1917;">{ptype["count"]}</span>
                                      </td>
                                    </tr>
                                  </table>
                                </td>
                              </tr>'''
        
        # Build price tier rows with progress bars
        price_tier_rows = ""
        total_tier_count = sum(t["count"] for t in price_tiers) or 1
        for tier in price_tiers:
            width_pct = int((tier["count"] / total_tier_count) * 100) if total_tier_count else 0
            price_tier_rows += f'''
                              <tr>
                                <td style="padding: 5px 0;">
                                  <table role="presentation" cellpadding="0" cellspacing="0" width="100%">
                                    <tr>
                                      <td style="vertical-align: middle;">
                                        <span style="font-size: 13px; color: #1c1917;">{tier["name"]}</span>
                                      </td>
                                      <td align="right" style="vertical-align: middle;">
                                        <span style="font-family: Georgia, 'Times New Roman', serif; font-size: 14px; font-weight: 700; color: #1c1917;">{tier["count"]}</span>
                                      </td>
                                    </tr>
                                  </table>
                                  <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="margin-top: 4px;">
                                    <tr>
                                      <td style="padding-right: 8px;">
                                        <div style="height: 6px; background-color: #f0f0f0; border-radius: 4px; overflow: hidden;">
                                          <div style="width: {width_pct}%; height: 6px; background-color: {primary_color}; border-radius: 4px;"></div>
                                        </div>
                                      </td>
                                      <td width="60" style="text-align: right;">
                                        <span style="font-size: 10px; color: #78716c;">{tier["range"]}</span>
                                      </td>
                                    </tr>
                                  </table>
                                </td>
                              </tr>'''
        
        # Side-by-side layout
        property_types_html = f'''
              <!-- V15: Property Types + Price Tiers (Side by Side) -->
              <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="margin-bottom: 28px;">
                <tr>
                  <!-- Property Types -->
                  <td width="48%" style="vertical-align: top; padding-right: 8px;">
                    <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="border: 1px solid #e7e5e4; border-radius: 8px; background-color: #ffffff;">
                      <tr>
                        <td style="padding: 16px;">
                          {_section_label_html("By Property Type", primary_color)}
                          <table role="presentation" cellpadding="0" cellspacing="0" width="100%">
                            {property_type_rows}
                          </table>
                        </td>
                      </tr>
                    </table>
                  </td>
                  <!-- Price Tiers -->
                  <td width="52%" style="vertical-align: top; padding-left: 8px;">
                    <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="border: 1px solid #e7e5e4; border-radius: 8px; background-color: #ffffff;">
                      <tr>
                        <td style="padding: 16px;">
                          {_section_label_html("By Price Range", primary_color)}
                          <table role="presentation" cellpadding="0" cellspacing="0" width="100%">
                            {price_tier_rows}
                          </table>
                        </td>
                      </tr>
                    </table>
                  </td>
                </tr>
              </table>
'''
        # price_tiers_html stays empty since it's combined above
    elif property_types:
        # Fallback: Property types only (full width)
        property_type_rows = ""
        for ptype in property_types:
            property_type_rows += f'''
                              <tr>
                                <td style="padding: 5px 0;">
                                  <table role="presentation" cellpadding="0" cellspacing="0" width="100%">
                                    <tr>
                                      <td style="vertical-align: middle;">
                                        <span style="font-size: 14px; color: {primary_color}40;">&#9632;</span>
                                        <span style="font-size: 13px; color: #1c1917; padding-left: 6px;">{ptype["name"]}</span>
                                      </td>
                                      <td align="right" style="vertical-align: middle;">
                                        <span style="font-family: Georgia, 'Times New Roman', serif; font-size: 14px; font-weight: 700; color: #1c1917;">{ptype["count"]}</span>
                                      </td>
                                    </tr>
                                  </table>
                                </td>
                              </tr>'''
        property_types_html = f'''
              <!-- V15: Property Types (full width) -->
              <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="margin-bottom: 28px;">
                <tr>
                  <td style="padding: 16px; border: 1px solid #e7e5e4; border-radius: 8px; background-color: #ffffff;">
                    {_section_label_html("By Property Type", primary_color)}
                    <table role="presentation" cellpadding="0" cellspacing="0" width="100%">
                      {property_type_rows}
                    </table>
                  </td>
                </tr>
              </table>
'''
    
    if price_tiers and not property_types:
        # Fallback: Price tiers only (full width)
        total_tier_count = sum(t["count"] for t in price_tiers) or 1
        price_tier_rows = ""
        for tier in price_tiers:
            width_pct = int((tier["count"] / total_tier_count) * 100) if total_tier_count else 0
            price_tier_rows += f'''
                              <tr>
                                <td style="padding: 5px 0;">
                                  <table role="presentation" cellpadding="0" cellspacing="0" width="100%">
                                    <tr>
                                      <td><span style="font-size: 13px; color: #1c1917;">{tier["name"]}</span></td>
                                      <td align="right"><span style="font-family: Georgia, 'Times New Roman', serif; font-size: 14px; font-weight: 700; color: #1c1917;">{tier["count"]}</span></td>
                                    </tr>
                                  </table>
                                  <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="margin-top: 4px;">
                                    <tr>
                                      <td style="padding-right: 8px;">
                                        <div style="height: 6px; background-color: #f0f0f0; border-radius: 4px; overflow: hidden;">
                                          <div style="width: {width_pct}%; height: 6px; background-color: {primary_color}; border-radius: 4px;"></div>
                                        </div>
                                      </td>
                                      <td width="60" style="text-align: right;"><span style="font-size: 10px; color: #78716c;">{tier["range"]}</span></td>
                                    </tr>
                                  </table>
                                </td>
                              </tr>'''
        price_tiers_html = f'''
              <!-- V15: Price Tiers (full width) -->
              <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="margin-bottom: 28px;">
                <tr>
                  <td style="padding: 16px; border: 1px solid #e7e5e4; border-radius: 8px; background-color: #ffffff;">
                    {_section_label_html("By Price Range", primary_color)}
                    <table role="presentation" cellpadding="0" cellspacing="0" width="100%">
                      {price_tier_rows}
                    </table>
                  </td>
                </tr>
              </table>
'''
    
    # V5: Build gallery grid HTML for gallery report types
    # V6: Pass preset_display_name for custom section titles
    gallery_html = ""
    if has_gallery:
        gallery_html = _build_gallery_grid_html(listings or [], report_type, primary_color, accent_color, preset_display_name)
    
    # V5: Build listings table HTML for inventory/new_listings/closed
    listings_table_html = ""
    if has_listings_table:
        listings_table_html = _build_listings_table_html(listings or [], report_type, primary_color)
    
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
  <meta name="color-scheme" content="light dark">
  <meta name="supported-color-schemes" content="light dark">
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
    
    /* Dark Mode */
    @media (prefers-color-scheme: dark) {{
      .dark-bg {{ background-color: #1a1a2e !important; }}
      .dark-text {{ color: #e5e5e5 !important; }}
      .dark-card {{ background-color: #262640 !important; }}
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
<body style="margin: 0; padding: 0; background-color: #f5f5f4; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;">
  
  <!-- Preheader Text (hidden preview text) -->
  <div style="display: none; max-height: 0; overflow: hidden; mso-hide: all;">
    {preheader} &nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;
  </div>
  
  <!-- Email Container -->
  <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="background-color: #f5f5f4;" class="dark-bg">
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
          
          <!-- ========== MAIN CONTENT ========== -->
          <tr>
            <td style="background-color: #ffffff; padding: 40px;" class="dark-card mobile-padding">
              
              {"" if has_hero_4 else f'''<!-- Section Label (V3 style) -->
              <table role="presentation" cellpadding="0" cellspacing="0" width="100%">
                <tr>
                  <td align="center" style="padding-bottom: 20px;">
                    <p style="margin: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; font-size: 11px; font-weight: 600; color: #64748b; text-transform: uppercase; letter-spacing: 1.5px;">
                      {section_label}
                    </p>
                  </td>
                </tr>
              </table>
'''}
{filter_description_html}{insight_html}{hero_4_html if has_hero_4 else f'''              <!-- ========== V10: 3-COLUMN METRICS (Professional) ========== -->
              <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="margin-bottom: 24px;">
                <tr>
                  <td>
                    <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="background-color: #fafaf9; border-radius: 8px; border: 1px solid #e7e5e4;">
                      <tr>
                        <td width="33%" align="center" style="padding: 20px 12px; border-right: 1px solid #e7e5e4;">
                          <p style="margin: 0 0 4px 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; font-size: 26px; font-weight: 700; color: #1c1917;">
                            {m1_value}
                          </p>
                          <p style="margin: 0; font-size: 10px; font-weight: 500; color: #78716c; text-transform: uppercase; letter-spacing: 0.5px;">
                            {m1_label}
                          </p>
                        </td>
                        <td width="34%" align="center" style="padding: 20px 12px; border-right: 1px solid #e7e5e4;">
                          <p style="margin: 0 0 4px 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; font-size: 26px; font-weight: 700; color: #1c1917;">
                            {m2_value}
                          </p>
                          <p style="margin: 0; font-size: 10px; font-weight: 500; color: #78716c; text-transform: uppercase; letter-spacing: 0.5px;">
                            {m2_label}
                          </p>
                        </td>
                        <td width="33%" align="center" style="padding: 20px 12px;">
                          <p style="margin: 0 0 4px 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; font-size: 26px; font-weight: 700; color: #1c1917;">
                            {m3_value}
                          </p>
                          <p style="margin: 0; font-size: 10px; font-weight: 500; color: #78716c; text-transform: uppercase; letter-spacing: 0.5px;">
                            {m3_label}
                          </p>
                        </td>
                      </tr>
                    </table>
                  </td>
                </tr>
              </table>
'''}{listings_table_html if report_type == "closed" else ""}{core_indicators_html if has_hero_4 else ""}{extra_stats_html}{property_types_html if report_type != "closed" else ""}{price_tiers_html if report_type != "closed" else ""}{price_bands_html}{gallery_html}{listings_table_html if report_type != "closed" else ""}
              <!-- V15: QUICK TAKE CALLOUT (accent card with icon) -->
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
                            {quick_take}
                          </p>
                        </td>
                      </tr>
                    </table>
                  </td>
                </tr>
              </table>

              <!-- V15: CTA AREA (tinted background) -->
              <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="margin-bottom: 28px;">
                <tr>
                  <td align="center" style="padding: 24px; background-color: {primary_color}0A; border-radius: 8px;">
                    <!--[if mso]>
                    <v:roundrect xmlns:v="urn:schemas-microsoft-com:vml" xmlns:w="urn:schemas-microsoft-com:office:word" href="{pdf_url}" style="height:48px;v-text-anchor:middle;width:220px;" arcsize="8%" stroke="f" fillcolor="{primary_color}">
                      <w:anchorlock/>
                      <center style="color:#ffffff;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Arial,sans-serif;font-size:14px;font-weight:600;">View Full Report</center>
                    </v:roundrect>
                    <![endif]-->
                    <!--[if !mso]><!-->
                    <a href="{pdf_url}" target="_blank" style="display: inline-block; background-color: {primary_color}; color: #ffffff; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; font-size: 14px; font-weight: 600; text-decoration: none; padding: 14px 36px; border-radius: 8px; letter-spacing: 0.3px;">
                      View Full Report
                    </a>
                    <!--<![endif]-->
                  </td>
                </tr>
              </table>
              
              <!-- Divider -->
              <table role="presentation" cellpadding="0" cellspacing="0" width="100%">
                <tr>
                  <td style="border-top: 1px solid #e5e7eb; padding-top: 32px;" class="dark-border"></td>
                </tr>
              </table>
              
{agent_footer_html}
              
            </td>
          </tr>
          
          <!-- ========== FOOTER ========== -->
          <tr>
            <td style="background-color: #f9fafb; padding: 24px 40px; border-radius: 0 0 12px 12px; border-top: 1px solid #e5e7eb;" class="dark-card dark-border mobile-padding">
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
