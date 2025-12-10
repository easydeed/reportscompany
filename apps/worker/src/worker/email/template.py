"""HTML email template for scheduled report notifications.

V2: Redesigned with V0-generated email-safe HTML template.
- Table-based layout for maximum email client compatibility
- MSO/Outlook conditional comments for rounded buttons
- VML fallback for Outlook
- Full white-label branding support
"""
from typing import Dict, Optional, TypedDict, Tuple


class Brand(TypedDict, total=False):
    """Brand configuration for white-label emails."""
    display_name: str
    logo_url: Optional[str]
    primary_color: Optional[str]
    accent_color: Optional[str]
    rep_photo_url: Optional[str]
    contact_line1: Optional[str]
    contact_line2: Optional[str]
    website_url: Optional[str]


# Report type display names - keep in sync with:
# - Frontend: apps/web/app/lib/reportTypes.ts
# - Backend: apps/api/src/api/routes/schedules.py
# - Worker: apps/worker/src/worker/report_builders.py
REPORT_TYPE_DISPLAY = {
    "market_snapshot": "Market Snapshot",
    "new_listings": "New Listings",
    "inventory": "Inventory Report",
    "closed": "Closed Sales",
    "price_bands": "Price Bands Analysis",
    "open_houses": "Open Houses",
    "new_listings_gallery": "New Listings Gallery",
    "featured_listings": "Featured Listings",
}


def _format_price(price: Optional[float]) -> str:
    """Format price for display."""
    if price is None:
        return "N/A"
    if price >= 1_000_000:
        return f"${price / 1_000_000:.1f}M"
    if price >= 1_000:
        return f"${price / 1_000:.0f}K"
    return f"${price:,.0f}"


def _format_number(value: Optional[int]) -> str:
    """Format number for display."""
    if value is None:
        return "N/A"
    return f"{value:,}"


def _get_metrics_for_report_type(
    report_type: str, 
    metrics: Dict
) -> Tuple[Tuple[str, str], Tuple[str, str], Tuple[str, str]]:
    """
    Get the 3 metrics to display based on report type.
    Returns: ((label1, value1), (label2, value2), (label3, value3))
    """
    # Extract common metrics with defaults
    total_active = metrics.get("total_active", 0)
    total_pending = metrics.get("total_pending", 0)
    total_closed = metrics.get("total_closed", 0)
    total_listings = metrics.get("total_listings", total_active)
    median_list_price = metrics.get("median_list_price")
    median_close_price = metrics.get("median_close_price")
    avg_dom = metrics.get("avg_dom")
    months_of_inventory = metrics.get("months_of_inventory")
    sale_to_list_ratio = metrics.get("sale_to_list_ratio")
    
    # Format DOM
    dom_display = f"{avg_dom:.0f}" if avg_dom else "N/A"
    
    if report_type == "market_snapshot":
        return (
            ("Active Listings", _format_number(total_active)),
            ("Pending", _format_number(total_pending)),
            ("Closed Sales", _format_number(total_closed)),
        )
    
    elif report_type == "new_listings":
        return (
            ("New Listings", _format_number(total_active)),
            ("Median Price", _format_price(median_list_price)),
            ("Avg. DOM", dom_display),
        )
    
    elif report_type == "closed":
        return (
            ("Closed Sales", _format_number(total_closed)),
            ("Median Price", _format_price(median_close_price)),
            ("Avg. DOM", dom_display),
        )
    
    elif report_type == "new_listings_gallery":
        return (
            ("📸 Properties", _format_number(total_listings)),
            ("Median Price", _format_price(median_list_price)),
            ("Avg. DOM", dom_display),
        )
    
    elif report_type == "featured_listings":
        return (
            ("✨ Featured", _format_number(total_listings)),
            ("Median Price", _format_price(median_list_price)),
            ("Avg. DOM", dom_display),
        )
    
    elif report_type == "inventory":
        moi_display = f"{months_of_inventory:.1f}" if months_of_inventory else "N/A"
        return (
            ("Active Inventory", _format_number(total_active)),
            ("Median Price", _format_price(median_list_price)),
            ("Months Supply", moi_display),
        )
    
    elif report_type == "price_bands":
        return (
            ("Total Listings", _format_number(total_active)),
            ("Median Price", _format_price(median_list_price)),
            ("Avg. DOM", dom_display),
        )
    
    elif report_type == "open_houses":
        return (
            ("Open Houses", _format_number(total_active)),
            ("Median Price", _format_price(median_list_price)),
            ("This Weekend", _format_number(metrics.get("weekend_count", 0))),
        )
    
    else:
        # Generic fallback
        return (
            ("Properties", _format_number(total_active)),
            ("Median Price", _format_price(median_list_price)),
            ("Avg. DOM", dom_display),
        )


def _get_section_label(report_type: str) -> str:
    """Get the section label above metrics based on report type."""
    labels = {
        "market_snapshot": "Market Snapshot",
        "new_listings": "New on Market",
        "closed": "Recently Sold",
        "new_listings_gallery": "Photo Gallery",
        "featured_listings": "Featured Properties",
        "inventory": "Current Inventory",
        "price_bands": "Price Analysis",
        "open_houses": "Open Houses",
    }
    return labels.get(report_type, "Market Overview")


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
    brand_name = (brand.get("display_name") if brand else None) or account_name or "Market Reports"
    logo_url = brand.get("logo_url") if brand else None
    primary_color = (brand.get("primary_color") if brand else None) or "#7C3AED"
    accent_color = (brand.get("accent_color") if brand else None) or "#F97316"
    rep_photo_url = brand.get("rep_photo_url") if brand else None
    contact_line1 = brand.get("contact_line1") if brand else None
    contact_line2 = brand.get("contact_line2") if brand else None
    website_url = brand.get("website_url") if brand else None
    
    # Format report type for display
    report_type_display = REPORT_TYPE_DISPLAY.get(
        report_type, 
        report_type.replace("_", " ").title()
    )
    
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
    
    # Get metrics for this report type
    (m1_label, m1_value), (m2_label, m2_value), (m3_label, m3_value) = \
        _get_metrics_for_report_type(report_type, metrics)
    
    # Get section label
    section_label = _get_section_label(report_type)
    
    # Build logo HTML (conditional)
    if logo_url:
        logo_html = f'''<img src="{logo_url}" alt="{brand_name}" width="180" height="50" style="display: block; max-width: 180px; height: auto;" />'''
    else:
        # Text fallback when no logo
        logo_html = f'''<p style="margin: 0; font-family: Arial, Helvetica, sans-serif; font-size: 24px; font-weight: 700; color: #ffffff;">{brand_name}</p>'''
    
    # Build footer section (conditional based on available data)
    if rep_photo_url and (contact_line1 or contact_line2):
        # Full footer with photo
        footer_html = f'''
              <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%">
                <tr>
                  <td width="80" valign="top" style="padding-right: 20px;">
                    <img src="{rep_photo_url}" alt="Agent Photo" width="70" height="70" style="display: block; width: 70px; height: 70px; border-radius: 50%; object-fit: cover;" />
                  </td>
                  <td valign="middle">
                    {f'<p style="margin: 0 0 4px 0; font-family: Arial, Helvetica, sans-serif; font-size: 15px; font-weight: 600; color: #1f2937; line-height: 1.4;">{contact_line1}</p>' if contact_line1 else ''}
                    {f'<p style="margin: 0 0 8px 0; font-family: Arial, Helvetica, sans-serif; font-size: 14px; color: #6b7280; line-height: 1.4;">{contact_line2}</p>' if contact_line2 else ''}
                    {f'<a href="{website_url}" target="_blank" style="font-family: Arial, Helvetica, sans-serif; font-size: 14px; color: {primary_color}; text-decoration: none; font-weight: 500;">{website_url.replace("https://", "").replace("http://", "")}</a>' if website_url else ''}
                  </td>
                </tr>
              </table>'''
    elif contact_line1 or contact_line2 or website_url:
        # Contact info without photo
        footer_html = f'''
              <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%">
                <tr>
                  <td align="center">
                    {f'<p style="margin: 0 0 4px 0; font-family: Arial, Helvetica, sans-serif; font-size: 15px; font-weight: 600; color: #1f2937; line-height: 1.4;">{contact_line1}</p>' if contact_line1 else ''}
                    {f'<p style="margin: 0 0 8px 0; font-family: Arial, Helvetica, sans-serif; font-size: 14px; color: #6b7280; line-height: 1.4;">{contact_line2}</p>' if contact_line2 else ''}
                    {f'<a href="{website_url}" target="_blank" style="font-family: Arial, Helvetica, sans-serif; font-size: 14px; color: {primary_color}; text-decoration: none; font-weight: 500;">{website_url.replace("https://", "").replace("http://", "")}</a>' if website_url else ''}
                  </td>
                </tr>
              </table>'''
    else:
        # Minimal footer - just brand name
        footer_html = f'''
              <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%">
                <tr>
                  <td align="center">
                    <p style="margin: 0; font-family: Arial, Helvetica, sans-serif; font-size: 15px; font-weight: 600; color: #1f2937; line-height: 1.4;">{brand_name}</p>
                  </td>
                </tr>
              </table>'''
    
    # Build powered by text (only show if not branded)
    powered_by = '' if brand else '''
                <p style="margin: 10px 0 0 0; font-family: Arial, Helvetica, sans-serif; font-size: 11px; color: #d1d5db;">
                  Powered by TrendyReports
                </p>'''
    
    # Build the complete HTML email
    html = f'''<!DOCTYPE html>
<html lang="en" xmlns="http://www.w3.org/1999/xhtml" xmlns:v="urn:schemas-microsoft-com:vml" xmlns:o="urn:schemas-microsoft-com:office:office">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta http-equiv="X-UA-Compatible" content="IE=edge">
  <meta name="x-apple-disable-message-reformatting">
  <title>{brand_name} - {report_type_display}</title>
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
</head>
<body style="margin: 0; padding: 0; background-color: #f4f4f4; font-family: Arial, Helvetica, sans-serif; -webkit-font-smoothing: antialiased; -moz-osx-font-smoothing: grayscale;">
  
  <!-- Wrapper Table -->
  <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="background-color: #f4f4f4;" bgcolor="#f4f4f4">
    <tr>
      <td align="center" style="padding: 20px 10px;">
        
        <!-- Main Container -->
        <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="600" style="max-width: 600px; background-color: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.1);" bgcolor="#ffffff">
          
          <!-- Header Section -->
          <tr>
            <td align="center" style="background-color: {primary_color}; padding: 30px 40px;" bgcolor="{primary_color}">
              <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%">
                <tr>
                  <td align="center" style="padding-bottom: 20px;">
                    {logo_html}
                  </td>
                </tr>
                <tr>
                  <td align="center">
                    <h1 style="margin: 0; font-family: Arial, Helvetica, sans-serif; font-size: 28px; font-weight: 700; color: #ffffff; line-height: 1.3;">
                      {report_type_display}
                    </h1>
                  </td>
                </tr>
                <tr>
                  <td align="center" style="padding-top: 10px;">
                    <p style="margin: 0; font-family: Arial, Helvetica, sans-serif; font-size: 16px; color: rgba(255,255,255,0.9); line-height: 1.5;">
                      {area_display} &bull; Last {lookback_days} Days
                    </p>
                  </td>
                </tr>
              </table>
            </td>
          </tr>
          
          <!-- Metrics Section -->
          <tr>
            <td style="padding: 40px 30px; background-color: #ffffff;" bgcolor="#ffffff">
              <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%">
                <tr>
                  <td align="center" style="padding-bottom: 20px;">
                    <p style="margin: 0; font-family: Arial, Helvetica, sans-serif; font-size: 14px; font-weight: 600; color: {accent_color}; text-transform: uppercase; letter-spacing: 1px;">
                      {section_label}
                    </p>
                  </td>
                </tr>
                <tr>
                  <td>
                    <!-- 3-Column Metrics Table -->
                    <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%">
                      <tr>
                        <!-- Metric 1 -->
                        <td width="32%" align="center" valign="top" style="padding: 20px 10px; background-color: #f9fafb; border-radius: 8px;" bgcolor="#f9fafb">
                          <table role="presentation" cellpadding="0" cellspacing="0" border="0">
                            <tr>
                              <td align="center">
                                <p style="margin: 0; font-family: Arial, Helvetica, sans-serif; font-size: 32px; font-weight: 700; color: {primary_color}; line-height: 1.2;">
                                  {m1_value}
                                </p>
                              </td>
                            </tr>
                            <tr>
                              <td align="center" style="padding-top: 8px;">
                                <p style="margin: 0; font-family: Arial, Helvetica, sans-serif; font-size: 13px; color: #6b7280; line-height: 1.4;">
                                  {m1_label}
                                </p>
                              </td>
                            </tr>
                          </table>
                        </td>
                        
                        <!-- Spacer -->
                        <td width="2%">&nbsp;</td>
                        
                        <!-- Metric 2 -->
                        <td width="32%" align="center" valign="top" style="padding: 20px 10px; background-color: #f9fafb; border-radius: 8px;" bgcolor="#f9fafb">
                          <table role="presentation" cellpadding="0" cellspacing="0" border="0">
                            <tr>
                              <td align="center">
                                <p style="margin: 0; font-family: Arial, Helvetica, sans-serif; font-size: 32px; font-weight: 700; color: {primary_color}; line-height: 1.2;">
                                  {m2_value}
                                </p>
                              </td>
                            </tr>
                            <tr>
                              <td align="center" style="padding-top: 8px;">
                                <p style="margin: 0; font-family: Arial, Helvetica, sans-serif; font-size: 13px; color: #6b7280; line-height: 1.4;">
                                  {m2_label}
                                </p>
                              </td>
                            </tr>
                          </table>
                        </td>
                        
                        <!-- Spacer -->
                        <td width="2%">&nbsp;</td>
                        
                        <!-- Metric 3 -->
                        <td width="32%" align="center" valign="top" style="padding: 20px 10px; background-color: #f9fafb; border-radius: 8px;" bgcolor="#f9fafb">
                          <table role="presentation" cellpadding="0" cellspacing="0" border="0">
                            <tr>
                              <td align="center">
                                <p style="margin: 0; font-family: Arial, Helvetica, sans-serif; font-size: 32px; font-weight: 700; color: {primary_color}; line-height: 1.2;">
                                  {m3_value}
                                </p>
                              </td>
                            </tr>
                            <tr>
                              <td align="center" style="padding-top: 8px;">
                                <p style="margin: 0; font-family: Arial, Helvetica, sans-serif; font-size: 13px; color: #6b7280; line-height: 1.4;">
                                  {m3_label}
                                </p>
                              </td>
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
          
          <!-- CTA Section -->
          <tr>
            <td align="center" style="padding: 10px 40px 40px 40px; background-color: #ffffff;" bgcolor="#ffffff">
              <table role="presentation" cellpadding="0" cellspacing="0" border="0">
                <tr>
                  <td align="center" style="background-color: {accent_color}; border-radius: 8px;" bgcolor="{accent_color}">
                    <!--[if mso]>
                    <v:roundrect xmlns:v="urn:schemas-microsoft-com:vml" xmlns:w="urn:schemas-microsoft-com:office:word" href="{pdf_url}" style="height:50px;v-text-anchor:middle;width:220px;" arcsize="16%" stroke="f" fillcolor="{accent_color}">
                      <w:anchorlock/>
                      <center>
                    <![endif]-->
                    <a href="{pdf_url}" target="_blank" style="display: inline-block; padding: 16px 40px; font-family: Arial, Helvetica, sans-serif; font-size: 16px; font-weight: 600; color: #ffffff; text-decoration: none; border-radius: 8px; background-color: {accent_color};">
                      View Full Report
                    </a>
                    <!--[if mso]>
                      </center>
                    </v:roundrect>
                    <![endif]-->
                  </td>
                </tr>
              </table>
            </td>
          </tr>
          
          <!-- Divider -->
          <tr>
            <td style="padding: 0 40px;">
              <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%">
                <tr>
                  <td style="border-top: 1px solid #e5e7eb; height: 1px; font-size: 1px; line-height: 1px;">&nbsp;</td>
                </tr>
              </table>
            </td>
          </tr>
          
          <!-- Footer Section -->
          <tr>
            <td style="padding: 40px; background-color: #ffffff;" bgcolor="#ffffff">
              {footer_html}
            </td>
          </tr>
          
          <!-- Unsubscribe Footer -->
          <tr>
            <td align="center" style="padding: 20px 40px; background-color: #f9fafb;" bgcolor="#f9fafb">
              <p style="margin: 0; font-family: Arial, Helvetica, sans-serif; font-size: 12px; color: #9ca3af; line-height: 1.6;">
                You're receiving this email because you subscribed to market updates.<br />
                <a href="{unsubscribe_url}" target="_blank" style="color: #6b7280; text-decoration: underline;">Unsubscribe</a> from these notifications.
              </p>{powered_by}
            </td>
          </tr>
          
        </table>
        <!-- End Main Container -->
        
      </td>
    </tr>
  </table>
  <!-- End Wrapper Table -->
  
</body>
</html>'''
    
    return html


def schedule_email_subject(
    report_type: str, 
    city: Optional[str], 
    zip_codes: Optional[list]
) -> str:
    """Generate email subject line for a scheduled report."""
    # Format report type
    report_type_display = REPORT_TYPE_DISPLAY.get(
        report_type, 
        report_type.replace("_", " ").title()
    )
    
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
    
    return f"📊 Your {report_type_display} Report for {area} is Ready!"
