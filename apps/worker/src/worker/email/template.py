"""HTML email template for scheduled report notifications.

V2: Complete redesign with V0-generated email-safe HTML template.
- Table-based layout for maximum email client compatibility
- MSO/Outlook conditional comments for rounded buttons and circular photos
- VML fallback for Outlook gradient headers
- Dark mode support
- Mobile responsive (metrics stack on mobile)
- Full white-label branding support
- Report-specific extra stats and price bands sections
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
REPORT_CONFIG = {
    "market_snapshot": {
        "label": "Market Snapshot",
        "tagline": "Your Complete Market Overview",
        "section": "Market Snapshot",
        "has_extra_stats": True,
    },
    "new_listings": {
        "label": "New Listings",
        "tagline": "Fresh Properties Just Listed",
        "section": "New on Market",
        "has_extra_stats": False,
    },
    "inventory": {
        "label": "Inventory Report",
        "tagline": "Current Market Availability",
        "section": "Current Inventory",
        "has_extra_stats": False,
    },
    "closed": {
        "label": "Closed Sales",
        "tagline": "Recent Sales Activity",
        "section": "Recently Sold",
        "has_extra_stats": True,
    },
    "price_bands": {
        "label": "Price Analysis",
        "tagline": "Market by Price Tier",
        "section": "Price Analysis",
        "has_extra_stats": False,
        "has_price_bands": True,
    },
    "open_houses": {
        "label": "Open Houses",
        "tagline": "Open This Weekend",
        "section": "Open Houses",
        "has_extra_stats": False,
    },
    "new_listings_gallery": {
        "label": "New Listings Gallery",
        "tagline": "The Newest Properties",
        "section": "Photo Gallery",
        "has_extra_stats": False,
    },
    "featured_listings": {
        "label": "Featured Listings",
        "tagline": "Premium Properties",
        "section": "Featured Properties",
        "has_extra_stats": False,
    },
}


def _format_price(price: Optional[float]) -> str:
    """Format price for display."""
    if price is None:
        return "N/A"
    if price >= 1_000_000:
        return f"${price / 1_000_000:.2f}M".rstrip('0').rstrip('.')  + "M" if price % 1_000_000 == 0 else f"${price / 1_000_000:.2f}M"
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


def _format_decimal(value: Optional[float], decimals: int = 1) -> str:
    """Format decimal for display."""
    if value is None:
        return "N/A"
    return f"{value:.{decimals}f}"


def _get_metrics_for_report_type(
    report_type: str, 
    metrics: Dict
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
        return (
            ("New Listings", _format_number(total_listings)),
            ("Median Price", _format_price_clean(median_list_price)),
            ("Starting At", _format_price_clean(metrics.get("min_price"))),
        )
    
    elif report_type == "featured_listings":
        return (
            ("Featured Homes", _format_number(total_listings)),
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
                    "color": "#10b981",  # Green
                },
                {
                    "name": "Move-Up",
                    "range": metrics.get("moveup_range", "Median - 75th"),
                    "count": metrics.get("moveup_count", 0),
                    "color": "PRIMARY",  # Will be replaced
                },
                {
                    "name": "Luxury",
                    "range": metrics.get("luxury_range", "75th+"),
                    "count": metrics.get("luxury_count", 0),
                    "color": "ACCENT",  # Will be replaced
                },
            ]
    
    # Map bands from metrics
    if bands:
        colors = ["#10b981", "PRIMARY", "ACCENT", "#f59e0b", "#ef4444"]
        return [
            {
                "name": b.get("name", f"Band {i+1}"),
                "range": b.get("range", ""),
                "count": b.get("count", 0),
                "color": colors[i % len(colors)],
            }
            for i, b in enumerate(bands)
        ]
    
    return None


def _build_preheader(report_type: str, area: str, metrics: Dict) -> str:
    """Build preheader text for email preview."""
    config = REPORT_CONFIG.get(report_type, {})
    label = config.get("label", "Report")
    
    # Get a key metric for the preheader
    if report_type == "market_snapshot":
        count = metrics.get("total_active", 0)
        return f"📊 {label} for {area}: {count} active listings, see median prices and market trends"
    elif report_type == "new_listings":
        count = metrics.get("total_active", 0)
        return f"🏠 {count} new listings in {area} - see prices, photos, and details"
    elif report_type == "closed":
        count = metrics.get("total_closed", 0)
        return f"🔑 {count} homes sold in {area} - see sale prices and market activity"
    elif report_type == "price_bands":
        return f"💰 Price analysis for {area} - see entry, move-up, and luxury tiers"
    elif report_type == "inventory":
        count = metrics.get("total_active", 0)
        return f"📋 {count} active listings in {area} - current market availability"
    else:
        return f"📊 Your {label} for {area} is ready to view"


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
) -> str:
    """
    Generate HTML email for a scheduled report notification.
    
    V2: Complete redesign with V0-generated email-safe template.
    Features:
    - Gradient header with Outlook VML fallback
    - Dark mode support
    - Mobile responsive (metrics stack)
    - Extra stats row for Market Snapshot & Closed Sales
    - Price bands section for Price Bands report
    - Preheader text for email preview
    - Polished agent footer with circular photo
    
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
    report_label = config.get("label")
    tagline = config.get("tagline")
    section_label = config.get("section")
    has_extra_stats = config.get("has_extra_stats", False)
    has_price_bands = config.get("has_price_bands", False)
    
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
    
    # Get metrics
    (m1_label, m1_value), (m2_label, m2_value), (m3_label, m3_value) = \
        _get_metrics_for_report_type(report_type, metrics)
    
    # Get extra stats if applicable
    extra_stats = _get_extra_stats(report_type, metrics) if has_extra_stats else None
    
    # Get price bands if applicable
    price_bands = _get_price_bands(metrics) if has_price_bands else None
    
    # Build preheader
    preheader = _build_preheader(report_type, area_display, metrics)
    
    # Build logo HTML for email header
    # Use email_logo_url if available (light version for gradient headers)
    # Otherwise, use logo_url (will be displayed on gradient, may need inversion via CSS)
    header_logo = email_logo_url or logo_url
    if header_logo:
        logo_html = f'<img src="{header_logo}" alt="{brand_name}" width="160" style="display: block; max-width: 160px; height: auto;">'
    else:
        logo_html = f'<span style="font-size: 24px; font-weight: 700; color: #ffffff;">{brand_name}</span>'
    
    # Build extra stats HTML
    extra_stats_html = ""
    if extra_stats:
        (es1_value, es1_label), (es2_value, es2_label) = extra_stats
        extra_stats_html = f'''
              <!-- Extra Stats Row -->
              <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="margin-bottom: 24px; background-color: {primary_color}08; border-radius: 10px;">
                <tr>
                  <td align="center" style="padding: 16px 20px;">
                    <span style="font-size: 14px; color: #4b5563;">
                      <strong style="color: {primary_color};">{es1_value}</strong> {es1_label}
                      &nbsp;&nbsp;|&nbsp;&nbsp;
                      <strong style="color: {accent_color};">{es2_value}</strong> {es2_label}
                    </span>
                  </td>
                </tr>
              </table>
'''
    
    # Build price bands HTML
    price_bands_html = ""
    if price_bands:
        bands_rows = ""
        for i, band in enumerate(price_bands):
            color = band["color"]
            if color == "PRIMARY":
                color = primary_color
            elif color == "ACCENT":
                color = accent_color
            
            border = 'border-bottom: 1px solid #e5e7eb;' if i < len(price_bands) - 1 else ''
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
                          <span style="font-size: 15px; font-weight: 600; color: #1f2937;">{band["name"]}</span>
                          <span style="font-size: 14px; color: #6b7280; margin-left: 8px;">{band["range"]}</span>
                        </td>
                        <td align="right" style="vertical-align: middle;">
                          <span style="font-size: 15px; font-weight: 600; color: {primary_color};">{band["count"]} listings</span>
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
                    <p style="margin: 0; font-size: 14px; font-weight: 600; color: #374151; text-transform: uppercase; letter-spacing: 0.5px;">
                      Price Tiers
                    </p>
                  </td>
                </tr>
                {bands_rows}
              </table>
'''
    
    # Build agent footer HTML
    if rep_photo_url and (contact_line1 or rep_name):
        # Full footer with photo
        contact_info = ""
        if rep_phone or rep_email:
            phone_html = f'<a href="tel:{rep_phone}" style="color: {primary_color}; text-decoration: none;">{rep_phone}</a>' if rep_phone else ""
            email_html = f'<a href="mailto:{rep_email}" style="color: {primary_color}; text-decoration: none;">{rep_email}</a>' if rep_email else ""
            separator = " &bull; " if phone_html and email_html else ""
            contact_info = f'''
                          <p style="margin: 0; font-size: 13px;">
                            {phone_html}{separator}{email_html}
                          </p>'''
        
        agent_footer_html = f'''
              <!-- Agent Footer -->
              <table role="presentation" cellpadding="0" cellspacing="0" width="100%">
                <tr>
                  <td align="center">
                    <table role="presentation" cellpadding="0" cellspacing="0">
                      <tr>
                        <!-- Agent Photo -->
                        <td style="vertical-align: middle; padding-right: 20px;">
                          <!--[if mso]>
                          <v:oval xmlns:v="urn:schemas-microsoft-com:vml" style="width:70px;height:70px;" stroke="f">
                            <v:fill type="frame" src="{rep_photo_url}"/>
                          </v:oval>
                          <![endif]-->
                          <!--[if !mso]><!-->
                          <img src="{rep_photo_url}" alt="{contact_line1 or rep_name}" width="70" height="70" style="display: block; width: 70px; height: 70px; border-radius: 50%; object-fit: cover; border: 3px solid {primary_color}20;">
                          <!--<![endif]-->
                        </td>
                        <!-- Agent Info -->
                        <td style="vertical-align: middle;">
                          <p style="margin: 0 0 2px 0; font-size: 17px; font-weight: 600; color: #1a1a2e;" class="dark-text">
                            {contact_line1 or rep_name}
                          </p>
                          {f'<p style="margin: 0 0 8px 0; font-size: 13px; color: #6b7280;">{contact_line2 or rep_title}</p>' if (contact_line2 or rep_title) else ''}
                          {contact_info}
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
<body style="margin: 0; padding: 0; background-color: #f4f4f7; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">
  
  <!-- Preheader Text (hidden preview text) -->
  <div style="display: none; max-height: 0; overflow: hidden; mso-hide: all;">
    {preheader} &nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;
  </div>
  
  <!-- Email Container -->
  <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="background-color: #f4f4f7;" class="dark-bg">
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
                  <td align="center" style="padding: 28px 40px;">
                    {logo_html}
                  </td>
                </tr>
                <tr>
                  <td align="center" style="padding: 0 40px 8px 40px;">
                    <span style="display: inline-block; background-color: rgba(255,255,255,0.2); color: #ffffff; font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 1.5px; padding: 6px 14px; border-radius: 20px;">
                      {report_label}
                    </span>
                  </td>
                </tr>
                <tr>
                  <td align="center" style="padding: 0 40px;">
                    <h1 style="margin: 0; font-size: 26px; font-weight: 700; color: #ffffff; line-height: 1.3;">
                      {tagline}
                    </h1>
                  </td>
                </tr>
                <tr>
                  <td align="center" style="padding: 10px 40px 28px 40px;">
                    <p style="margin: 0; font-size: 15px; color: rgba(255,255,255,0.9);">
                      {area_display} &bull; {date_range}
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
          
          <!-- ========== MAIN CONTENT ========== -->
          <tr>
            <td style="background-color: #ffffff; padding: 40px;" class="dark-card mobile-padding">
              
              <!-- Section Label -->
              <table role="presentation" cellpadding="0" cellspacing="0" width="100%">
                <tr>
                  <td align="center" style="padding-bottom: 20px;">
                    <p style="margin: 0; font-size: 12px; font-weight: 600; color: {accent_color}; text-transform: uppercase; letter-spacing: 1px;">
                      {section_label}
                    </p>
                  </td>
                </tr>
              </table>
              
              <!-- ========== 3-COLUMN METRICS ========== -->
              <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="margin-bottom: 24px;">
                <tr>
                  <!-- Metric 1 -->
                  <td width="33%" class="metric-card" style="padding: 0 6px;">
                    <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="background-color: #f9fafb; border-radius: 12px; border: 1px solid #e5e7eb;" class="dark-card dark-border">
                      <tr>
                        <td align="center" style="padding: 20px 12px;">
                          <p style="margin: 0 0 4px 0; font-size: 28px; font-weight: 700; color: {primary_color};">
                            {m1_value}
                          </p>
                          <p style="margin: 0; font-size: 12px; font-weight: 500; color: #6b7280; text-transform: uppercase; letter-spacing: 0.5px;">
                            {m1_label}
                          </p>
                        </td>
                      </tr>
                    </table>
                  </td>
                  <!-- Metric 2 -->
                  <td width="33%" class="metric-card" style="padding: 0 6px;">
                    <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="background-color: #f9fafb; border-radius: 12px; border: 1px solid #e5e7eb;" class="dark-card dark-border">
                      <tr>
                        <td align="center" style="padding: 20px 12px;">
                          <p style="margin: 0 0 4px 0; font-size: 28px; font-weight: 700; color: {accent_color};">
                            {m2_value}
                          </p>
                          <p style="margin: 0; font-size: 12px; font-weight: 500; color: #6b7280; text-transform: uppercase; letter-spacing: 0.5px;">
                            {m2_label}
                          </p>
                        </td>
                      </tr>
                    </table>
                  </td>
                  <!-- Metric 3 -->
                  <td width="33%" class="metric-card" style="padding: 0 6px;">
                    <table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="background-color: #f9fafb; border-radius: 12px; border: 1px solid #e5e7eb;" class="dark-card dark-border">
                      <tr>
                        <td align="center" style="padding: 20px 12px;">
                          <p style="margin: 0 0 4px 0; font-size: 28px; font-weight: 700; color: #10b981;">
                            {m3_value}
                          </p>
                          <p style="margin: 0; font-size: 12px; font-weight: 500; color: #6b7280; text-transform: uppercase; letter-spacing: 0.5px;">
                            {m3_label}
                          </p>
                        </td>
                      </tr>
                    </table>
                  </td>
                </tr>
              </table>
              
{extra_stats_html}{price_bands_html}
              <!-- ========== CTA BUTTON ========== -->
              <table role="presentation" cellpadding="0" cellspacing="0" width="100%">
                <tr>
                  <td align="center" style="padding: 8px 0 32px 0;">
                    <!--[if mso]>
                    <v:roundrect xmlns:v="urn:schemas-microsoft-com:vml" xmlns:w="urn:schemas-microsoft-com:office:word" href="{pdf_url}" style="height:50px;v-text-anchor:middle;width:220px;" arcsize="50%" stroke="f" fillcolor="{primary_color}">
                      <w:anchorlock/>
                      <center style="color:#ffffff;font-family:sans-serif;font-size:16px;font-weight:600;">View Full Report</center>
                    </v:roundrect>
                    <![endif]-->
                    <!--[if !mso]><!-->
                    <a href="{pdf_url}" target="_blank" style="display: inline-block; background: linear-gradient(135deg, {primary_color} 0%, {accent_color} 100%); color: #ffffff; font-size: 16px; font-weight: 600; text-decoration: none; padding: 14px 36px; border-radius: 50px; box-shadow: 0 4px 14px {primary_color}40;">
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
